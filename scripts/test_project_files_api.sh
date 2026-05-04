#!/usr/bin/env bash
# scripts/test_project_files_api.sh
# Tests the project files API: GET and POST /api/projects/{id}/files/

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/project_files_cookies.txt"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() { echo -e "\n${GREEN}==> $1${NC}"; }
print_error() { echo -e "${RED}ERROR: $1${NC}"; }
print_info() { echo -e "${YELLOW}INFO: $1${NC}"; }

# Cleanup cookies on exit
trap 'rm -f "${COOKIE_FILE}"' EXIT

# Helper to call API
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
}

# Helper to parse JSON
json_get() {
    local key="$1"
    local body="$2"
    printf '%s' "$body" | python3 -c "import sys, json; data=sys.stdin.read(); val=json.loads(data).get('$key', ''); print(json.dumps(val) if isinstance(val, (dict, list)) else val)" 2>/dev/null || echo ""
}

# 1. Register & Login
print_step "1) Authentication"
EMAIL="file_test_$(date +%s)@example.com"
USERNAME="file_user_$(date +%s)"
PASSWORD="PassWord123!"

call_api "POST" "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
call_api "POST" "/api/auth/login/" "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
if [[ "$HTTP_STATUS" != "200" ]]; then print_error "Login failed"; exit 1; fi

# 2. Setup Project
print_step "2) Project Setup"
call_api "POST" "/api/orgs/organizations/" "{\"name\":\"File Test Org\"}"
ORG_ID=$(json_get "id" "$HTTP_BODY")
call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"File Test Workspace\", \"organization\":\"${ORG_ID}\"}"
WS_ID=$(json_get "id" "$HTTP_BODY")
call_api "POST" "/api/projects/" "{\"name\":\"File Test Project\", \"workspace_id\":\"${WS_ID}\"}"
PROJ_ID=$(json_get "id" "$HTTP_BODY")
print_info "Project ID: $PROJ_ID"

# 3. Test File Creation (POST)
print_step "3) Testing File Creation: POST /api/projects/${PROJ_ID}/files/"
# Note: Real file upload would use multipart, but here we simulate with JSON payload as implemented in views
call_api "POST" "/api/projects/${PROJ_ID}/files/" "{\"file_name\":\"spec.pdf\", \"file_url\":\"http://storage.local/spec.pdf\", \"mime_type\":\"application/pdf\", \"file_size\":1024}"
if [[ "$HTTP_STATUS" == "201" ]]; then
    echo "Success: Project file metadata created."
    FILE_ID=$(json_get "id" "$HTTP_BODY")
    print_info "File ID: $FILE_ID"
else
    print_error "File creation failed"
    echo "$HTTP_BODY"
    exit 1
fi

# 4. Test File List (GET)
print_step "4) Testing File List: GET /api/projects/${PROJ_ID}/files/"
call_api "GET" "/api/projects/${PROJ_ID}/files/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Files listed."
    if [[ "$HTTP_BODY" == *"$FILE_ID"* ]]; then
        echo "Validated: Created file exists in the list."
    else
        print_error "Created file NOT found in list"
        exit 1
    fi
else
    print_error "File listing failed"
    exit 1
fi

# 5. Test File Detail (GET)
print_step "5) Testing File Detail"
call_api "GET" "/api/projects/${PROJ_ID}/files/${FILE_ID}/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: File detail retrieved."
else
    print_error "File detail failed"
    exit 1
fi

# 6. Test File Delete
print_step "6) Testing File Delete"
call_api "DELETE" "/api/projects/${PROJ_ID}/files/${FILE_ID}/"
if [[ "$HTTP_STATUS" == "204" ]]; then
    echo "Success: File deleted."
else
    print_error "File deletion failed"
    exit 1
fi

echo -e "\n${GREEN}Project Files API test suite completed successfully!${NC}"
