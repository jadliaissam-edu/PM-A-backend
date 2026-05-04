#!/usr/bin/env bash
# scripts/test_ticket_import.sh

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/import_cookies.txt"

# Helper to call API
call_api() {
    local method="$1"
    local endpoint="$2"
    local payload="${3:-}"

    echo -e "\n[$method] $endpoint" >&2
    if [[ -z "$payload" ]]; then
        curl -sS -H "Content-Type: application/json" -b "$COOKIE_FILE" -c "$COOKIE_FILE" -X "$method" "$BASE_URL$endpoint"
    else
        curl -sS -H "Content-Type: application/json" -b "$COOKIE_FILE" -c "$COOKIE_FILE" -X "$method" -d "$payload" "$BASE_URL$endpoint"
    fi
}

json_get() {
    local key="$1"
    local body="$2"
    printf '%s' "$body" | python3 -c "import sys, json; data=sys.stdin.read(); val=json.loads(data).get('$key', ''); print(json.dumps(val) if isinstance(val, (dict, list)) else val)" 2>/dev/null || echo ""
}

echo "1) Auth"
TS=$(date +%s)
call_api "POST" "/api/auth/register/" "{\"username\":\"imp_${TS}\",\"email\":\"imp_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null
call_api "POST" "/api/auth/login/" "{\"email\":\"imp_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Setup Org/WS/Project"
ORG_ID=$(call_api "POST" "/api/orgs/organizations/" '{"name":"Import Org"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
WS_ID=$(call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Import WS\", \"organization\":\"$ORG_ID\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
PROJ_ID=$(call_api "POST" "/api/projects/" "{\"name\":\"Import Project\", \"workspace_id\":\"$WS_ID\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "3) Test CSV Import"
cat > /tmp/test_tickets.csv <<EOF
title,description,priority,type
"CSV Ticket 1","Desc 1","high","bug"
"CSV Ticket 2","Desc 2","medium","story"
EOF

# Use multipart/form-data for file upload
curl -sS -b "$COOKIE_FILE" -X POST \
     -F "file=@/tmp/test_tickets.csv" \
     -F "format=csv" \
     "$BASE_URL/api/projects/$PROJ_ID/tickets/import/"

echo -e "\n4) Test Markdown Import"
cat > /tmp/test_tickets.md <<EOF
# Backend Tasks
- [ ] MD Ticket 1
- [ ] MD Ticket 2
EOF

curl -sS -b "$COOKIE_FILE" -X POST \
     -F "file=@/tmp/test_tickets.md" \
     -F "format=markdown" \
     "$BASE_URL/api/projects/$PROJ_ID/tickets/import/"

echo -e "\n5) Verify Tickets created"
call_api "GET" "/api/projects/$PROJ_ID/tickets/"

rm -f "$COOKIE_FILE" /tmp/test_tickets.csv /tmp/test_tickets.md
