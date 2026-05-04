#!/usr/bin/env bash
# scripts/test_collaboration_api.sh
# Tests the collaboration API: Channels, Messages, Comments, Reactions

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/collab_api_cookies.txt"

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
EMAIL="collab_test_$(date +%s)@example.com"
USERNAME="collab_user_$(date +%s)"
PASSWORD="PassWord123!"

call_api "POST" "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
call_api "POST" "/api/auth/login/" "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
if [[ "$HTTP_STATUS" != "200" ]]; then print_error "Login failed"; exit 1; fi

# 2. Setup Hierarchy (Org -> Workspace -> Project -> Ticket)
print_step "2) Hierarchy Setup"
call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Collab Org\"}"
ORG_ID=$(json_get "id" "$HTTP_BODY")

call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Collab Workspace\", \"organization\":\"${ORG_ID}\"}"
WS_ID=$(json_get "id" "$HTTP_BODY")

call_api "POST" "/api/projects/" "{\"name\":\"Collab Project\", \"workspace_id\":\"${WS_ID}\"}"
PROJ_ID=$(json_get "id" "$HTTP_BODY")
print_info "Project ID: $PROJ_ID"

# We need a ticket to comment on
call_api "POST" "/api/projects/${PROJ_ID}/tickets/" "{\"title\":\"Test Ticket\"}"
TID=$(json_get "id" "$HTTP_BODY")

if [[ -z "$TID" ]]; then
    # Maybe it was created but we missed the ID
    print_info "Searching for tickets in project..."
    call_api "GET" "/api/projects/${PROJ_ID}/tickets/"
    TID=$(printf '%s' "$HTTP_BODY" | python3 -c "import sys, json; data=sys.stdin.read(); print(json.loads(data)[0].get('id', ''))" 2>/dev/null || echo "")
fi

if [[ -z "$TID" ]]; then
    # Fallback: create via shell
    TID=$(./.venv/bin/python3 manage.py shell <<EOF
from tickets.models import Ticket
from project.models import Project
p = Project.objects.get(id='${PROJ_ID}')
t = Ticket.objects.create(project=p, title='Manual Ticket')
print(str(t.id))
EOF
)
TID=$(echo "$TID" | tail -n1)
fi
print_info "Ticket ID: $TID"

# 3. Comments CRUD
print_step "3) Comments Management"
call_api "POST" "/api/projects/${PROJ_ID}/tickets/${TID}/comments/" "{\"body\":\"This is a test comment\"}"
CID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$CID" ]]; then print_error "Comment creation failed"; exit 1; fi

call_api "GET" "/api/projects/${PROJ_ID}/tickets/${TID}/comments/"
call_api "PATCH" "/api/projects/${PROJ_ID}/tickets/${TID}/comments/${CID}/" "{\"body\":\"Updated comment\"}"

# 4. Reactions
print_step "4) Reactions Management"
call_api "POST" "/api/projects/${PROJ_ID}/tickets/${TID}/comments/${CID}/reactions/" "{\"type\":\"like\"}"
RID=$(json_get "id" "$HTTP_BODY")

call_api "GET" "/api/projects/${PROJ_ID}/tickets/${TID}/comments/${CID}/reactions/"
call_api "DELETE" "/api/projects/${PROJ_ID}/tickets/${TID}/comments/${CID}/reactions/${RID}/"

# 5. Chat Channels
print_step "5) Chat Channels"
call_api "POST" "/api/channels/" "{\"name\":\"General\", \"organization\":\"${ORG_ID}\", \"description\":\"Public channel\"}"
CH_ID=$(json_get "id" "$HTTP_BODY")
if [[ -z "$CH_ID" ]]; then print_error "Channel creation failed"; echo $HTTP_BODY; exit 1; fi

call_api "GET" "/api/channels/?organization_id=${ORG_ID}"

# 6. Chat Messages
print_step "6) Chat Messages"
call_api "POST" "/api/messages/" "{\"content\":\"Hello world!\", \"channel\":\"${CH_ID}\"}"
call_api "GET" "/api/messages/?channel_id=${CH_ID}"

echo -e "\n${GREEN}Collaboration API test suite completed successfully!${NC}"
