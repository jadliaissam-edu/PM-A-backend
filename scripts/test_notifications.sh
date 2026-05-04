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
USER_BODY=$(call_api "POST" "/api/auth/register/" "{\"username\":\"nu_${TS}\",\"email\":\"nu_${TS}@example.com\",\"password\":\"PassWord123!\"}")
call_api "POST" "/api/auth/login/" "{\"email\":\"nu_${TS}@example.com\",\"password\":\"PassWord123!\"}" > /dev/null

echo "2) Check Initial Unread Count"
call_api "GET" "/api/notifications/unread-count/"

echo "3) Create some notifications manually (via shell)"
/home/snofy/project_matier/PM-A-backend/.venv/bin/python3 manage.py shell <<EOF
from django.contrib.auth import get_user_model
from core.models import NotificationEvent
import uuid
User = get_user_model()
user = User.objects.get(username='nu_${TS}')
for i in range(3):
    NotificationEvent.objects.create(
        user=user,
        project_id=uuid.uuid4(),
        event_type="test_event",
        payload_json={"msg": f"Test {i}"}
    )
EOF

echo "4) Check Unread Count again"
COUNT_BODY=$(call_api "GET" "/api/notifications/unread-count/")
echo "$COUNT_BODY"

echo "5) Get Notification IDs"
LIST_BODY=$(call_api "GET" "/api/notifications/")
# Extract IDs (hacky way for test)
N1_ID=$(echo "$LIST_BODY" | grep -oP '"id":"\K[^"]+' | head -n1)
N2_ID=$(echo "$LIST_BODY" | grep -oP '"id":"\K[^"]+' | head -n2 | tail -n1)

echo "6) Mark Bulk Read (N1, N2)"
call_api "POST" "/api/notifications/mark-read-bulk/" "{\"notification_ids\":[\"$N1_ID\", \"$N2_ID\"]}"

echo "7) Final Unread Count"
call_api "GET" "/api/notifications/unread-count/"

rm -f "$COOKIE_FILE"
