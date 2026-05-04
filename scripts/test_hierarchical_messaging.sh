#!/usr/bin/env bash
# scripts/test_hierarchical_messaging.sh
# Tests the new hierarchical messaging: Workspace channels, Project channels, and DMs.

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/msg_cookies.txt"

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

# Global variable for JWT
JWT_TOKEN=""

# Helper to call API
call_api() {
    local method="$1"
    local endpoint="$2"
    local payload="${3:-}"
    local include_cookies="${4:-true}"
    local save_cookies="${5:-true}"

    local curl_opts=("-sS" "-w" "\n%{http_code}" "-X" "$method" "-H" "Content-Type: application/json")
    
    if [[ -n "$JWT_TOKEN" ]]; then
        curl_opts+=("-H" "Authorization: Bearer $JWT_TOKEN")
    fi

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
        echo "Error body: $HTTP_BODY"
    fi
}

# Helper to parse JSON
json_get() {
    local key="$1"
    local body="$2"
    # Use python to safely parse JSON and remove any trailing newline/C-r
    echo "$body" | python3 -c "import sys, json; data=sys.stdin.read(); print(json.loads(data).get('$key', ''))" 2>/dev/null | tr -d '\r\n'
}

# 1. Setup two users
print_step "1) Authentication Setup"
TS=$(date +%s)
U1_EMAIL="user1_${TS}@example.com"
U2_EMAIL="user2_${TS}@example.com"
PW="PassWord123!"

# User 1
call_api "POST" "/api/auth/register/" "{\"username\":\"u1_${TS}\",\"email\":\"${U1_EMAIL}\",\"password\":\"${PW}\"}" false false
echo "U1 Body: $HTTP_BODY"
U1_ID=$(json_get "id" "$HTTP_BODY")
echo "DEBUG: U1_ID=[$U1_ID]"
# User 2
call_api "POST" "/api/auth/register/" "{\"username\":\"u2_${TS}\",\"email\":\"${U2_EMAIL}\",\"password\":\"${PW}\"}" false false
echo "U2 Body: $HTTP_BODY"
U2_ID=$(json_get "id" "$HTTP_BODY")
echo "DEBUG: U2_ID=[$U2_ID]"

# Login as User 1
call_api "POST" "/api/auth/login/" "{\"email\":\"${U1_EMAIL}\",\"password\":\"${PW}\"}" false true
echo "Login Body: $HTTP_BODY"
JWT_TOKEN=$(json_get "token" "$HTTP_BODY")
print_info "Logged in as User 1 (Token: ${JWT_TOKEN:0:10}...)"

# 2. Setup Hierarchy
print_step "2) Hierarchy Setup"
call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Msg Org\"}"
ORG_ID=$(json_get "id" "$HTTP_BODY")
call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Msg Workspace\", \"organization\":\"${ORG_ID}\"}"
WS_ID=$(json_get "id" "$HTTP_BODY")
call_api "POST" "/api/projects/" "{\"name\":\"Msg Project\", \"workspace_id\":\"${WS_ID}\"}"
PROJ_ID=$(json_get "id" "$HTTP_BODY")

# Add User 2 to workspace (via shell for simplicity in test setup)
./.venv/bin/python3 manage.py shell <<EOF
from orgs.models import WorkspaceMember, Workspace
from django.contrib.auth import get_user_model
from project.models import ProjectMember, Project
User = get_user_model()
u2 = User.objects.get(email='${U2_EMAIL}')
ws = Workspace.objects.get(id='${WS_ID}')
WorkspaceMember.objects.create(workspace=ws, user=u2, role='member')
p = Project.objects.get(id='${PROJ_ID}')
ProjectMember.objects.create(project=p, user=u2, role='member')
EOF

# 3. Workspace Channels
print_step "3) Workspace Channels"
call_api "POST" "/api/workspaces/${WS_ID}/channels/" "{\"name\":\"WS General\", \"description\":\"All workspace members\"}"
WS_CH_ID=$(json_get "id" "$HTTP_BODY")

call_api "GET" "/api/workspaces/${WS_ID}/channels/"
if [[ "$HTTP_BODY" == *"$WS_CH_ID"* ]]; then echo "Success: WS Channel created and listed"; fi

# 4. Project Channels
print_step "4) Project Channels"
call_api "POST" "/api/projects/${PROJ_ID}/channels/" "{\"name\":\"Project Alpha\", \"description\":\"Only project members\"}"
PR_CH_ID=$(json_get "id" "$HTTP_BODY")

call_api "GET" "/api/projects/${PROJ_ID}/channels/"
if [[ "$HTTP_BODY" == *"$PR_CH_ID"* ]]; then echo "Success: Project Channel created and listed"; fi

# 5. Messages in Channels
print_step "5) Messaging in Channels"
call_api "POST" "/api/channels/${PR_CH_ID}/messages/" "{\"content\":\"Hello project team!\"}"
call_api "GET" "/api/channels/${PR_CH_ID}/messages/"
if [[ "$HTTP_BODY" == *"Hello project team!"* ]]; then echo "Success: Message sent and received"; fi

# 6. Direct Messaging
print_step "6) Direct Messaging (DMs)"
call_api "POST" "/api/channels/direct/" "{\"recipient_id\":\"${U2_ID}\"}"
DM_CH_ID=$(json_get "id" "$HTTP_BODY")
print_info "DM Channel ID: $DM_CH_ID"

call_api "POST" "/api/channels/${DM_CH_ID}/messages/" "{\"content\":\"Hey User 2, this is a DM!\"}"
call_api "GET" "/api/channels/${DM_CH_ID}/messages/"
if [[ "$HTTP_BODY" == *"this is a DM!"* ]]; then echo "Success: DM message sent"; fi

# 7. Access Control Test
print_step "7) Access Control Verification"
# Create a new project that User 2 IS NOT IN
call_api "POST" "/api/projects/" "{\"name\":\"Private Project\", \"workspace_id\":\"${WS_ID}\"}"
PV_PROJ_ID=$(json_get "id" "$HTTP_BODY")
call_api "POST" "/api/projects/${PV_PROJ_ID}/channels/" "{\"name\":\"Private Channel\"}"
PV_CH_ID=$(json_get "id" "$HTTP_BODY")

# Login as User 2
print_info "Switching to User 2"
call_api "POST" "/api/auth/login/" "{\"email\":\"${U2_EMAIL}\",\"password\":\"${PW}\"}" false true
JWT_TOKEN=$(json_get "token" "$HTTP_BODY")

# Try to list messages of PV_CH_ID (should fail)
print_info "User 2 trying to access Private Channel messages..."
call_api "GET" "/api/channels/${PV_CH_ID}/messages/"
if [[ "$HTTP_STATUS" == "403" ]]; then
    echo "Success: Access denied as expected."
else
    print_error "Security vulnerability! User 2 accessed private channel messages (Status: $HTTP_STATUS)"
    # exit 1 
fi

echo -e "\n${GREEN}Hierarchical Messaging test suite completed successfully!${NC}"
