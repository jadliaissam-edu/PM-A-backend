#!/usr/bin/env bash
# scripts/test_role_api.sh
# Tests the new role API endpoints defined in role/urls.py

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/role_api_cookies.txt"

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

# 1. Register & Login Owner
print_step "1) Setup Owner"
OWNER_EMAIL="owner_$(date +%s)@example.com"
OWNER_USER="owner_$(date +%s)"
PASSWORD="PassWord123!"

call_api "POST" "/api/auth/register/" "{\"username\":\"${OWNER_USER}\",\"email\":\"${OWNER_EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
call_api "POST" "/api/auth/login/" "{\"email\":\"${OWNER_EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
OWNER_ID=$(json_get "user_id" "$HTTP_BODY")
print_info "Owner ID: $OWNER_ID"

# 2. Register a Second User (Member)
print_step "2) Setup Member User"
MEMBER_EMAIL="member_$(date +%s)@example.com"
MEMBER_USER="member_$(date +%s)"
call_api "POST" "/api/auth/register/" "{\"username\":\"${MEMBER_USER}\",\"email\":\"${MEMBER_EMAIL}\",\"password\":\"${PASSWORD}\"}" false false
# Login to get Member ID
call_api "POST" "/api/auth/login/" "{\"email\":\"${MEMBER_EMAIL}\",\"password\":\"${PASSWORD}\"}" false false
MEMBER_ID=$(json_get "user_id" "$HTTP_BODY")
print_info "Member ID: $MEMBER_ID"

# 3. Login back as Owner for subsequent operations
print_step "3) Login as Owner"
call_api "POST" "/api/auth/login/" "{\"email\":\"${OWNER_EMAIL}\",\"password\":\"${PASSWORD}\"}" false true

# 4. Setup Project
print_step "4) Create Org -> Workspace -> Project"
call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Role Test Org\"}"
ORG_ID=$(json_get "id" "$HTTP_BODY")

call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Role Test Workspace\", \"organization\":\"${ORG_ID}\"}"
WORKSPACE_ID=$(json_get "id" "$HTTP_BODY")

call_api "POST" "/api/projects/" "{\"name\":\"Role Test Project\", \"workspace_id\":\"${WORKSPACE_ID}\"}"
PROJECT_ID=$(json_get "id" "$HTTP_BODY")
print_info "Project ID: $PROJECT_ID"

# 4. Test Role Creation (POST)
print_step "4) Testing Role Creation: POST /api/projects/${PROJECT_ID}/roles/"
call_api "POST" "/api/projects/${PROJECT_ID}/roles/" "{\"user\":\"${MEMBER_ID}\", \"role_name\":\"dev\", \"permissions\":[\"read\", \"write\"]}"
if [[ "$HTTP_STATUS" == "201" ]]; then
    echo "Success: Role created."
    ROLE_ID=$(json_get "id" "$HTTP_BODY")
    print_info "Role ID: $ROLE_ID"
else
    print_error "Role creation failed"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 5. Test Role Listing (GET)
print_step "5) Testing Role Listing: GET /api/projects/${PROJECT_ID}/roles/"
call_api "GET" "/api/projects/${PROJECT_ID}/roles/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Roles listed."
    # Check if our role is in the list
    if [[ "$HTTP_BODY" == *"$ROLE_ID"* ]]; then
        echo "Validated: Created role exists in the list."
    else
        print_error "Created role NOT found in list"
        echo "Body: $HTTP_BODY"
        exit 1
    fi
else
    print_error "Role listing failed"
    exit 1
fi

# 6. Test Role Update (PATCH)
print_step "6) Testing Role Update: PATCH /api/projects/${PROJECT_ID}/roles/${ROLE_ID}/"
call_api "PATCH" "/api/projects/${PROJECT_ID}/roles/${ROLE_ID}/" "{\"role_name\":\"admin\"}"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Role updated."
    NEW_ROLE_NAME=$(json_get "role_name" "$HTTP_BODY")
    if [[ "$NEW_ROLE_NAME" == "admin" ]]; then
        echo "Validated: role_name is now admin."
    else
        print_error "role_name was not updated correctly: $NEW_ROLE_NAME"
        exit 1
    fi
else
    print_error "Role update failed"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 7. Test Role Deletion (DELETE)
print_step "7) Testing Role Deletion: DELETE /api/projects/${PROJECT_ID}/roles/${ROLE_ID}/"
call_api "DELETE" "/api/projects/${PROJECT_ID}/roles/${ROLE_ID}/"
if [[ "$HTTP_STATUS" == "204" ]]; then
    echo "Success: Role deleted."
else
    print_error "Role deletion failed"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 8. Verify Deletion
print_step "8) Verifying Deletion"
call_api "GET" "/api/projects/${PROJECT_ID}/roles/"
if [[ "$HTTP_BODY" == *"$ROLE_ID"* ]]; then
    print_error "Role still exists after deletion!"
    exit 1
else
    echo "Success: Role confirmed gone."
fi

echo -e "\n${GREEN}New Role API test completed successfully!${NC}"
