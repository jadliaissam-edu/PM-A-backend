#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
COOKIE_FILE="/tmp/search_cookies.txt"

# Helper to call API
call_api() {
    local method=$1
    local endpoint=$2
    local payload=$3
    
    echo -e "\n[$method] $endpoint"
    if [[ -z "$payload" ]]; then
        curl -sS -H "Content-Type: application/json" -b "$COOKIE_FILE" -c "$COOKIE_FILE" -X "$method" "$BASE_URL$endpoint"
    else
        curl -sS -H "Content-Type: application/json" -b "$COOKIE_FILE" -c "$COOKIE_FILE" -X "$method" -d "$payload" "$BASE_URL$endpoint"
    fi
}

json_get() {
    local key=$1
    local body=$2
    echo "$body" | sed -n "s/.*\"$key\":\s*\"\?\([^\",}]*\)\"\?.*/\1/p" | head -n1
}

echo "1) Setup Auth"
TS=$(date +%s)
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"su_${TS}\",\"email\":\"su_${TS}@example.com\",\"password\":\"PassWord123!\"}")
call_api "POST" "/api/auth/login/" "{\"email\":\"su_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Create Workspace and Project"
WS_BODY=$(call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Search WS ${TS}\", \"organization\":\"1375a10c-15d6-44b3-8bc2-05e5ef6b0e75\"}") # Use a known org id or create one
# Actually better create an org
ORG_BODY=$(call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Search Org ${TS}\"}")
ORG_ID=$(json_get "id" "$ORG_BODY")
WS_BODY=$(call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Search WS ${TS}\", \"organization\":\"$ORG_ID\"}")
WS_ID=$(json_get "id" "$WS_BODY")
PROJ_BODY=$(call_api "POST" "/api/projects/" "{\"workspace\":\"$WS_ID\",\"name\":\"Search Project ${TS}\"}")
PROJ_ID=$(json_get "id" "$PROJ_BODY")

echo "3) Create Tickets"
call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Build the frontend dashboard\", \"description_markdown\":\"Need to use React and Recharts\"}"
call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Fix backend authentication\", \"description_markdown\":\"JWT tokens are not refreshing\"}"

echo "4) Search for 'dashboard'"
call_api "GET" "/api/search/?q=dashboard"

echo "5) Search for 'authentication'"
call_api "GET" "/api/search/?q=authentication"

rm -f "$COOKIE_FILE"
