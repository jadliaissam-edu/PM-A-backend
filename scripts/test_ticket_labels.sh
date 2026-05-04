#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
COOKIE_FILE="/tmp/msg_cookies.txt"

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
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"lu_${TS}\",\"email\":\"lu_${TS}@example.com\",\"password\":\"PassWord123!\"}")
call_api "POST" "/api/auth/login/" "{\"email\":\"lu_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Create Workspace and Project"
WS_BODY=$(call_api "POST" "/api/organizations/" "{\"name\":\"Label WS ${TS}\"}")
WS_ID=$(json_get "id" "$WS_BODY")
PROJ_BODY=$(call_api "POST" "/api/projects/" "{\"workspace\":\"$WS_ID\",\"name\":\"Label Project ${TS}\"}")
PROJ_ID=$(json_get "id" "$PROJ_BODY")

echo "3) Create Ticket"
TICKET_BODY=$(call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Label Test Ticket\"}")
TICKET_ID=$(json_get "id" "$TICKET_BODY")

echo "4) Add label 'critical'"
call_api "POST" "/api/projects/$PROJ_ID/tickets/$TICKET_ID/labels/" "{\"label\":\"critical\"}"

echo "5) Add multiple labels"
call_api "POST" "/api/projects/$PROJ_ID/tickets/$TICKET_ID/labels/" "{\"labels\":[\"urgent\", \"UI\"]}"

echo "6) Get labels"
call_api "GET" "/api/projects/$PROJ_ID/tickets/$TICKET_ID/labels/"

echo "7) Remove label 'urgent'"
call_api "POST" "/api/projects/$PROJ_ID/tickets/$TICKET_ID/labels/" "{\"action\":\"remove\",\"label\":\"urgent\"}"

echo "8) Set labels to ['final']"
call_api "POST" "/api/projects/$PROJ_ID/tickets/$TICKET_ID/labels/" "{\"action\":\"set\",\"labels\":[\"final\"]}"

rm -f "$COOKIE_FILE"
