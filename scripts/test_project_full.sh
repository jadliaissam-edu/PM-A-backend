#!/usr/bin/env bash
# scripts/test_project_full.sh
# Comprehensive test for project, dashboard, boards, and sprints API.

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="proj_test_$(date +%s)@example.com"
USERNAME="proj_user_$(date +%s)"
PASSWORD="PassWord123!"
COOKIE_FILE="/tmp/project_api_cookies.txt"

# Cleanup cookies on exit
trap 'rm -f "${COOKIE_FILE}"' EXIT

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() { echo -e "\n${GREEN}==> $1${NC}"; }
print_error() { echo -e "${RED}ERROR: $1${NC}"; }
print_info() { echo -e "${YELLOW}INFO: $1${NC}"; }

# Helper to call API
# Usage: call_api <METHOD> <ENDPOINT> [PAYLOAD] [INCLUDE_COOKIES] [SAVE_COOKIES]
call_api() {
    local method="$1"
    local endpoint="$2"
    local payload="${3:-}"
    local include_cookies="${4:-true}"
    local save_cookies="${5:-true}"

    local curl_opts=("-sS" "-w" "\n%{http_code}" "-X" "$method" "-H" "Content-Type: application/json")
    
    if [[ "$include_cookies" == "true" && -f "${COOKIE_FILE}" ]]; then
        curl_opts+=("-b" "${COOKIE_FILE}")
    fi
    
    if [[ "$save_cookies" == "true" ]]; then
        curl_opts+=("-c" "${COOKIE_FILE}")
    fi

    local response
    if [[ -z "$payload" ]]; then
        response=$(curl "${curl_opts[@]}" "${BASE_URL}${endpoint}")
    else
        response=$(curl "${curl_opts[@]}" -d "$payload" "${BASE_URL}${endpoint}")
    fi

    HTTP_STATUS=$(echo "${response}" | tail -n1)
    HTTP_BODY=$(echo "${response}" | sed '$d')

    echo "[$method] $endpoint -> $HTTP_STATUS"
    if [[ "$HTTP_STATUS" -ge 400 ]]; then
        echo "Response Body (first 200 chars): $(echo "$HTTP_BODY" | head -c 200)..."
    fi
}

# Helper to parse JSON
json_get() {
    local key="$1"
    local body="$2"
    printf '%s' "$body" | python3 -c "import sys, json; data=sys.stdin.read(); val=json.loads(data).get('$key', ''); print(json.dumps(val) if isinstance(val, (dict, list)) else val)" 2>/dev/null || echo ""
}

# START TESTS

# 1. Register & Login
print_step "1) Authentication"
call_api "POST" "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
if [[ "$HTTP_STATUS" != "201" ]]; then print_error "Register failed"; exit 1; fi

call_api "POST" "/api/auth/login/" "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
if [[ "$HTTP_STATUS" != "200" ]]; then print_error "Login failed"; exit 1; fi
USER_ID=$(json_get "user_id" "$HTTP_BODY")
print_info "Logged in as User ID: $USER_ID"

# 2. Setup Hierarchy (Org -> Workspace)
print_step "2) Hierarchy Setup"
call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Test Organization\"}"
ORG_ID=$(json_get "id" "$HTTP_BODY")
print_info "Org ID: $ORG_ID"

call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Test Workspace\", \"organization\":\"${ORG_ID}\"}"
WORKSPACE_ID=$(json_get "id" "$HTTP_BODY")
print_info "Workspace ID: $WORKSPACE_ID"

# 3. Project CRUD
print_step "3) Project Management"
call_api "POST" "/api/projects/" "{\"name\":\"Test Project\", \"description\":\"Testing all endpoints\", \"workspace_id\":\"${WORKSPACE_ID}\"}"
PROJECT_ID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$PROJECT_ID" ]]; then print_error "Project creation failed"; echo $HTTP_BODY; exit 1; fi
print_info "Project ID: $PROJECT_ID"

call_api "GET" "/api/projects/"
call_api "GET" "/api/projects/${PROJECT_ID}/"
call_api "PATCH" "/api/projects/${PROJECT_ID}/" "{\"description\":\"Updated description\"}"

# 4. Project Members & Roles
print_step "4) Members & Roles"
call_api "GET" "/api/projects/${PROJECT_ID}/members/"
# Roles use the same model ProjectMember
call_api "GET" "/api/projects/${PROJECT_ID}/roles/"

# 5. Boards & Columns
print_step "5) Boards & Columns"
call_api "GET" "/api/projects/${PROJECT_ID}/board/"
BOARD_ID=$(printf '%s' "$HTTP_BODY" | python3 -c "import sys, json; data=sys.stdin.read(); print(json.loads(data).get('board', {}).get('id', ''))")
print_info "Board ID: $BOARD_ID"

call_api "POST" "/api/projects/${PROJECT_ID}/board/columns/" "{\"name\":\"QA\", \"position\": 4}"
COL_ID=$(json_get "id" "$HTTP_BODY")
print_info "New Column ID: $COL_ID"

call_api "PATCH" "/api/projects/${PROJECT_ID}/board/columns/${COL_ID}/" "{\"name\":\"Quality Assurance\"}"
call_api "GET" "/api/projects/${PROJECT_ID}/board/stats/"
call_api "GET" "/api/projects/${PROJECT_ID}/board/task-summary/"
call_api "PATCH" "/api/projects/${PROJECT_ID}/board/config/" "{\"board_type\":\"kanban\"}"

# 6. Sprints
print_step "6) Sprints"
# Sprints endpoint is api/projects/<pid>/sprints/
call_api "POST" "/api/projects/${PROJECT_ID}/sprints/" "{\"name\":\"Sprint 1\", \"goal\":\"Finish tests\", \"start_date\":\"2026-05-01\", \"end_date\":\"2026-05-14\"}"
SPRINT_ID=$(json_get "id" "$HTTP_BODY")
print_info "Sprint ID: $SPRINT_ID"

call_api "GET" "/api/projects/${PROJECT_ID}/sprints/"
call_api "GET" "/api/projects/${PROJECT_ID}/sprints/${SPRINT_ID}/"
call_api "POST" "/api/projects/${PROJECT_ID}/sprints/${SPRINT_ID}/start/"
call_api "POST" "/api/projects/${PROJECT_ID}/sprints/${SPRINT_ID}/complete/"
# Sprint report might fail if no reports generated yet but testing reachability
call_api "GET" "/api/projects/${PROJECT_ID}/sprints/${SPRINT_ID}/report/"

# 7. Dashboard & Reports
print_step "7) Dashboards & Reports"
call_api "GET" "/api/dashboard/"
call_api "GET" "/api/dashboard/stats/"
call_api "GET" "/api/dashboard/projects/"
call_api "GET" "/api/dashboard/recent-projects/"
call_api "GET" "/api/projects/${PROJECT_ID}/reports/progress/"
call_api "GET" "/api/projects/${PROJECT_ID}/sprints/${SPRINT_ID}/reports/progress/"
call_api "GET" "/api/projects/${PROJECT_ID}/members/${USER_ID}/reports/progress/"

# 8. Documents
print_step "8) Project Documents"
call_api "POST" "/api/projects/${PROJECT_ID}/documents/" "{\"title\":\"Requirements\", \"content\":\"Test content\"}"
DOC_ID=$(json_get "id" "$HTTP_BODY")
print_info "Document ID: $DOC_ID"

call_api "GET" "/api/projects/${PROJECT_ID}/documents/"
call_api "GET" "/api/projects/${PROJECT_ID}/documents/${DOC_ID}/"
call_api "PATCH" "/api/projects/${PROJECT_ID}/documents/${DOC_ID}/" "{\"title\":\"Updated Requirements\"}"
call_api "DELETE" "/api/projects/${PROJECT_ID}/documents/${DOC_ID}/"

# 9. Cleanup & Finish
print_step "9) Cleanup & Finish"
call_api "POST" "/api/projects/${PROJECT_ID}/archive/"
call_api "POST" "/api/projects/${PROJECT_ID}/close/"
call_api "DELETE" "/api/projects/${PROJECT_ID}/"

echo -e "\n${GREEN}Project API test suite completed!${NC}"
