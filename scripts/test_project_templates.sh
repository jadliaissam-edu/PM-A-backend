#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
COOKIE_FILE="/tmp/template_cookies.txt"

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
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"tu_${TS}\",\"email\":\"tu_${TS}@example.com\",\"password\":\"PassWord123!\"}")
call_api "POST" "/api/auth/login/" "{\"email\":\"tu_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Create Organization"
ORG_BODY=$(call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Template Org ${TS}\"}")
ORG_ID=$(json_get "id" "$ORG_BODY")

echo "3) Create Workspace"
WS_BODY=$(call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Template WS ${TS}\", \"organization\": \"$ORG_ID\"}")
WS_ID=$(json_get "id" "$WS_BODY")

echo "4) Create Scrum Project (Template 1)"
call_api "POST" "/api/projects/from-template/" "{\"template_id\": 1, \"project_name\": \"Scrum SaaS\", \"workspace_id\": \"$WS_ID\"}"

echo "5) Create DevOps Project (Template 4)"
call_api "POST" "/api/projects/from-template/" "{\"template_id\": 4, \"project_name\": \"Infra DevOps\", \"workspace_id\": \"$WS_ID\"}"

rm -f "$COOKIE_FILE"
