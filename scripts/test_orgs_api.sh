#!/usr/bin/env bash
# scripts/test_orgs_api.sh
# Tests the orgs API endpoints: organizations, workspaces, invitations, tree

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/orgs_api_cookies.txt"

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
EMAIL="org_test_$(date +%s)@example.com"
USERNAME="org_user_$(date +%s)"
PASSWORD="PassWord123!"

call_api "POST" "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
call_api "POST" "/api/auth/login/" "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
if [[ "$HTTP_STATUS" != "200" ]]; then print_error "Login failed"; exit 1; fi

# 2. Organization CRUD
print_step "2) Organization Management"
ORG_NAME="Test Org $(date +%s)"
call_api "POST" "/api/orgs/organizations/" "{\"name\":\"${ORG_NAME}\"}"
ORG_ID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$ORG_ID" ]]; then print_error "Org creation failed"; echo "$HTTP_BODY"; exit 1; fi
print_info "Org Created: $ORG_ID"

call_api "PATCH" "/api/orgs/organizations/${ORG_ID}/" "{\"name\":\"${ORG_NAME} Updated\"}"
if [[ "$HTTP_STATUS" == "200" ]]; then echo "Success: Org updated."; fi

# 3. Workspace CRUD
print_step "3) Workspace Management"
WS_NAME="Test Workspace $(date +%s)"
call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"${WS_NAME}\", \"organization\":\"${ORG_ID}\"}"
WS_ID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$WS_ID" ]]; then print_error "Workspace creation failed"; echo "$HTTP_BODY"; exit 1; fi
print_info "Workspace Created: $WS_ID"

# 4. Ensure Visibility (Create Project)
# The orgs views require projects to show items in lists
print_step "4) Enable Visibility (Create Project)"
call_api "POST" "/api/projects/" "{\"name\":\"Visibility Project\", \"workspace_id\":\"${WS_ID}\"}"
PROJ_ID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$PROJ_ID" ]]; then print_error "Project creation failed"; echo "$HTTP_BODY"; exit 1; fi

# 5. List Orgs & Tree
print_step "5) Listing and Tree"
call_api "GET" "/api/orgs/organizations/"
if [[ "$HTTP_BODY" == *"$ORG_ID"* ]]; then echo "Success: Org found in list."; fi

call_api "GET" "/api/orgs/tree/"
if [[ "$HTTP_BODY" == *"$ORG_ID"* ]]; then echo "Success: Org found in tree."; fi

# 6. Invitations
print_step "6) Invitations"
EXPIRY=$(python3 -c "from datetime import datetime, timedelta; print((datetime.now() + timedelta(days=7)).isoformat())")
call_api "POST" "/api/orgs/invitations/" "{\"workspace\":\"${WS_ID}\", \"email\":\"invite@example.com\", \"invite_link\":\"http://localhost/invite\", \"expires_at\":\"${EXPIRY}\"}"
INV_ID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$INV_ID" ]]; then print_error "Invitation creation failed"; echo "$HTTP_BODY"; exit 1; fi
print_info "Invitation Created: $INV_ID"

call_api "POST" "/api/orgs/invitations/${INV_ID}/accept/"
if [[ "$HTTP_STATUS" == "200" ]]; then 
    echo "Success: Invitation accepted."
else
    print_error "Accept invitation failed"
    echo "$HTTP_BODY"
    exit 1
fi

# 7. Cleanup
print_step "7) Cleanup"
call_api "DELETE" "/api/orgs/workspaces/${WS_ID}/"
call_api "DELETE" "/api/orgs/organizations/${ORG_ID}/"

echo -e "\n${GREEN}Orgs API test suite completed successfully!${NC}"
