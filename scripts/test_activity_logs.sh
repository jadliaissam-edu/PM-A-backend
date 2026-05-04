#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
COOKIE_FILE="/tmp/activity_cookies.txt"

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
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"au_${TS}\",\"email\":\"au_${TS}@example.com\",\"password\":\"PassWord123!\"}")
call_api "POST" "/api/auth/login/" "{\"email\":\"au_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Create Workspace and Project"
WS_BODY=$(call_api "POST" "/api/organizations/" "{\"name\":\"Activity WS ${TS}\"}")
WS_ID=$(json_get "id" "$WS_BODY")
PROJ_BODY=$(call_api "POST" "/api/projects/" "{\"workspace\":\"$WS_ID\",\"name\":\"Activity Project ${TS}\"}")
PROJ_ID=$(json_get "id" "$PROJ_BODY")

echo "3) Create Ticket and Change Status"
TICKET_BODY=$(call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Activity Test Ticket\"}")
TICKET_ID=$(json_get "id" "$TICKET_BODY")
call_api "POST" "/api/projects/$PROJ_ID/tickets/$TICKET_ID/status/" "{\"status\":\"in_progress\"}"

echo "4) Add Comment"
call_api "POST" "/api/collaboration/projects/$PROJ_ID/tickets/$TICKET_ID/comments/" "{\"entity_type\":\"ticket\", \"entity_id\":\"$TICKET_ID\", \"body\":\"Test activity comment\"}"

echo "5) Check Project Activity"
call_api "GET" "/api/activity/projects/$PROJ_ID/activity/"

echo "6) Check Ticket History"
call_api "GET" "/api/activity/tickets/$TICKET_ID/history/"

echo "7) Check My Activity"
call_api "GET" "/api/activity/users/me/activity/"

rm -f "$COOKIE_FILE"
