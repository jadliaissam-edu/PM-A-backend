#!/usr/bin/env bash
# scripts/test_core_api.sh
# Tests the core API endpoints: spaces and notifications

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
COOKIE_FILE="/tmp/core_api_cookies.txt"

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
EMAIL="core_test_$(date +%s)@example.com"
USERNAME="core_user_$(date +%s)"
PASSWORD="PassWord123!"

call_api "POST" "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
call_api "POST" "/api/auth/login/" "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" false true
if [[ "$HTTP_STATUS" != "200" ]]; then print_error "Login failed"; echo "$HTTP_BODY"; exit 1; fi
USER_ID=$(json_get "user_id" "$HTTP_BODY")

# 2. Inject Data via Django Shell
print_step "2) Injecting Test Data"
./.venv/bin/python3 manage.py shell <<EOF
from core.models import Space, NotificationEvent
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()
user = User.objects.get(id=${USER_ID})

# Create spaces if none exist
if not Space.objects.exists():
    Space.objects.create(name="Dev Ops", description="Operations and Deployment", members=5, tasks=12, updated="2 hours ago", status="Healthy", color="bg-blue-500")
    Space.objects.create(name="Frontend", description="UI/UX Development", members=8, tasks=24, updated="1 day ago", status="Busy", color="bg-purple-500")

# Create a notification
NotificationEvent.objects.create(
    user=user,
    project_id=uuid.uuid4(),
    event_type="issue_created",
    payload_json={"title": "Test notification", "message": "Someone added a task"},
    is_read=False
)
print("Data injected successfully")
EOF

# 3. Test Spaces
print_step "3) Testing Spaces: GET /api/core/spaces/"
call_api "GET" "/api/core/spaces/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Spaces retrieved."
    # echo "Body: $HTTP_BODY"
else
    print_error "Failed to retrieve spaces"
    exit 1
fi

# 4. Test Notifications List
print_step "4) Testing Notifications: GET /api/core/notifications/"
call_api "GET" "/api/core/notifications/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Notifications retrieved."
    NOTIF_ID=$(printf '%s' "$HTTP_BODY" | python3 -c "import sys, json; data=sys.stdin.read(); print(json.loads(data)[0].get('id', ''))")
    if [[ -z "$NOTIF_ID" ]]; then
        print_error "No notification found in response"
        exit 1
    fi
    print_info "Notification ID: $NOTIF_ID"
else
    print_error "Failed to retrieve notifications"
    echo "$HTTP_BODY"
    exit 1
fi

# 5. Mark Notification as Read
print_step "5) Testing Mark Read: POST /api/core/notifications/${NOTIF_ID}/read/"
call_api "POST" "/api/core/notifications/${NOTIF_ID}/read/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Notification marked as read."
else
    print_error "Failed to mark notification as read"
    echo "$HTTP_BODY"
    exit 1
fi

# 6. Mark All as Read
print_step "6) Testing Mark All Read: POST /api/core/notifications/read-all/"
call_api "POST" "/api/core/notifications/read-all/"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: All notifications marked as read."
else
    print_error "Failed to mark all as read"
    echo "$HTTP_BODY"
    exit 1
fi

echo -e "\n${GREEN}Core API test suite completed successfully!${NC}"
