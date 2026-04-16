#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="${EMAIL:-hassinetrigui5@gmail.com}"
USERNAME="${USERNAME:-newuser1}"
INITIAL_PASSWORD="${INITIAL_PASSWORD:-StrongPass123!}"
NEW_PASSWORD="${NEW_PASSWORD:-NewStrongPass123!}"

print_step() {
  echo
  echo "==> $1"
}

user_exists() { 
    call_api "/api/auth/login/" "{\"username\":\"${USERNAME}\",\"password\":\"${INITIAL_PASSWORD}\"}"
    [[ "${HTTP_STATUS}" == "200" ]] 
}
create_user() {
  call_api "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${INITIAL_PASSWORD}\"}"
} 

call_api() {
  local endpoint="$1"
  local payload="$2"

  local response
  response=$(curl -sS -w '\n%{http_code}' -X POST "${BASE_URL}${endpoint}" \
    -H "Content-Type: application/json" \
    -d "${payload}")

  HTTP_STATUS=$(echo "${response}" | tail -n1)
  HTTP_BODY=$(echo "${response}" | sed '$d')

  echo "Status: ${HTTP_STATUS}"
  echo "Body  : ${HTTP_BODY}"
}

json_get() {
  local key="$1"
  local body="$2"
  python3 - <<PY
import json
try:
    obj = json.loads('''${body}''')
    value = obj.get('${key}', '')
    print(value if value is not None else '')
except Exception:
    print('')
PY
}

print_step "1) Register user (safe to run multiple times)"

create_user || echo "User may already exist, continuing with test..."

print_step "2) Request reset-password OTP"
call_api "/api/auth/reset-password/" "{\"email\":\"${EMAIL}\"}"
if [[ "${HTTP_STATUS}" != "200" ]]; then
  echo "Reset-password failed. Stop."
  exit 1
fi

OTP=$(json_get "otp" "${HTTP_BODY}")
if [[ -z "${OTP}" ]]; then
  echo "No OTP returned in JSON (likely real email mode)."
  read -r -p "Enter OTP from your email inbox: " OTP
fi

if [[ -z "${OTP}" ]]; then
  echo "OTP is empty. Stop."
  exit 1
fi

echo "Using OTP: ${OTP}"

print_step "3) Verify OTP"
call_api "/api/auth/reset-password/verify-otp/" "{\"email\":\"${EMAIL}\",\"otp\":\"${OTP}\"}"
if [[ "${HTTP_STATUS}" != "200" ]]; then
  echo "OTP verification failed. Stop."
  exit 1
fi

print_step "4) Confirm new password"
call_api "/api/auth/reset-password/confirm/" "{\"email\":\"${EMAIL}\",\"otp\":\"${OTP}\",\"new_password\":\"${NEW_PASSWORD}\"}"
if [[ "${HTTP_STATUS}" != "200" ]]; then
  echo "Password reset confirm failed. Stop."
  exit 1
fi

print_step "5) Login with new password"
call_api "/api/auth/login/" "{\"username\":\"${USERNAME}\",\"password\":\"${NEW_PASSWORD}\"}"

if [[ "${HTTP_STATUS}" == "200" ]]; then
  echo
  echo "Auth flow completed successfully."
else
  echo
  echo "Login failed. Check username/password or endpoint config."
  exit 1
fi
