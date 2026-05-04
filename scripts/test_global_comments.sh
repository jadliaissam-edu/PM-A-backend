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

# Helper to parse JSON (simple sed/grep version)
json_get() {
    local key=$1
    local body=$2
    echo "$body" | sed -n "s/.*\"$key\":\s*\"\?\([^\",}]*\)\"\?.*/\1/p" | head -n1
}

echo "1) Setup Auth"
TS=$(date +%s)
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"cu_${TS}\",\"email\":\"cu_${TS}@example.com\",\"password\":\"PassWord123!\"}")
echo "$USER_BODY"

call_api "POST" "/api/auth/login/" "{\"email\":\"cu_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Create Workspace and Project"
WS_BODY=$(call_api "POST" "/api/organizations/" "{\"name\":\"Comment WS ${TS}\"}")
WS_ID=$(json_get "id" "$WS_BODY")
echo "Workspace ID: $WS_ID"

PROJ_BODY=$(call_api "POST" "/api/projects/" "{\"workspace\":\"$WS_ID\",\"name\":\"Comment Project ${TS}\"}")
PROJ_ID=$(json_get "id" "$PROJ_BODY")
echo "Project ID: $PROJ_ID"

echo "3) Create Ticket"
TICKET_BODY=$(call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Comment Test Ticket\"}")
TICKET_ID=$(json_get "id" "$TICKET_BODY")
echo "Ticket ID: $TICKET_ID"

echo "4) Create Comment on Ticket via Global API"
GLOBAL_COMMENT_BODY=$(call_api "POST" "/api/comments/" "{\"entity_type\":\"ticket\",\"entity_id\":\"$TICKET_ID\",\"body\":\"First global comment on ticket\"}")
echo "$GLOBAL_COMMENT_BODY"

echo "5) Create Document"
DOC_BODY=$(call_api "POST" "/api/projects/$PROJ_ID/documents/" "{\"title\":\"Docs\",\"content\":\"Some content\"}")
DOC_ID=$(json_get "id" "$DOC_BODY")
echo "Document ID: $DOC_ID"

echo "6) Create Comment on Document"
DOC_COMMENT_BODY=$(call_api "POST" "/api/comments/" "{\"entity_type\":\"document\",\"entity_id\":\"$DOC_ID\",\"body\":\"Comment on document\"}")
echo "$DOC_COMMENT_BODY"

echo "7) List Comments for Document"
call_api "GET" "/api/comments/?entity_type=document&entity_id=$DOC_ID"

echo "8) Create Chat Channel and Message"
CH_BODY=$(call_api "POST" "/api/projects/$PROJ_ID/channels/" "{\"name\":\"General\"}")
CH_ID=$(json_get "id" "$CH_BODY")
echo "Channel ID: $CH_ID"

MSG_BODY=$(call_api "POST" "/api/channels/$CH_ID/messages/" "{\"content\":\"Hello World\"}")
MSG_ID=$(json_get "id" "$MSG_BODY")
echo "Message ID: $MSG_ID"

echo "9) Create Comment on Message"
MSG_COMMENT_BODY=$(call_api "POST" "/api/comments/" "{\"entity_type\":\"message\",\"entity_id\":\"$MSG_ID\",\"body\":\"Thread comment on message\"}")
echo "$MSG_COMMENT_BODY"

echo "10) List All Comments"
call_api "GET" "/api/comments/"

rm -f "$COOKIE_FILE"
