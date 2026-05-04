#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
COOKIE_FILE="/tmp/analytics_cookies.txt"

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

echo "1) Setup Auth"
TS=$(date +%s)
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"au_${TS}\",\"email\":\"au_${TS}@example.com\",\"password\":\"PassWord123!\"}")
call_api "POST" "/api/auth/login/" "{\"email\":\"au_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Create Workspace"
ORG_BODY=$(call_api "POST" "/api/orgs/organizations/" "{\"name\":\"Analytics Org ${TS}\"}")
ORG_ID=$(json_get "id" "$ORG_BODY")
WS_BODY=$(call_api "POST" "/api/orgs/workspaces/" "{\"name\":\"Analytics WS ${TS}\", \"organization\":\"$ORG_ID\"}")
WS_ID=$(json_get "id" "$WS_BODY")

echo "3) Create Scrum Project"
PROJ_BODY=$(call_api "POST" "/api/projects/from-template/" "{\"template_id\": 1, \"project_name\": \"Sprint Test\", \"workspace_id\": \"$WS_ID\"}")
PROJ_PART=$(json_get "project" "$PROJ_BODY")
PROJ_ID=$(json_get "id" "$PROJ_PART")

echo "DEBUG: PROJ_ID=$PROJ_ID"

echo "4) Create Sprint"
SPRINT_BODY=$(call_api "POST" "/api/projects/$PROJ_ID/sprints/" "{\"name\":\"Sprint 1\", \"start_date\":\"2026-05-01\", \"end_date\":\"2026-05-14\"}")
SPRINT_ID=$(json_get "id" "$SPRINT_BODY")

echo "DEBUG: SPRINT_ID=$SPRINT_ID"

echo "5) Add Tickets to Sprint"
T1=$(call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Task 1\", \"estimate_story_points\": 5, \"sprint\": \"$SPRINT_ID\", \"status\":\"done\"}")
T2=$(call_api "POST" "/api/projects/$PROJ_ID/tickets/" "{\"title\":\"Task 2\", \"estimate_story_points\": 3, \"sprint\": \"$SPRINT_ID\", \"status\":\"todo\"}")

echo "6) Complete Sprint"
call_api "POST" "/api/projects/$PROJ_ID/sprints/$SPRINT_ID/complete/"

echo "7) Verify Analytics"
call_api "GET" "/api/projects/$PROJ_ID/sprints/$SPRINT_ID/"

rm -f "$COOKIE_FILE"
