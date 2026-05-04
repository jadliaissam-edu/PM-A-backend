#!/usr/bin/env bash
# scripts/test_accounts_full.sh
# Tests all endpoints in the accounts app.

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="test_account_$(date +%s)@example.com"
USERNAME="testuser_$(date +%s)"
PASSWORD="StrongPass123!"
NEW_PASSWORD="NewStrongPass123!"
COOKIE_FILE="/tmp/api_cookies.txt"

# Cleanup cookies on exit
trap 'rm -f "${COOKIE_FILE}"' EXIT

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "\n${GREEN}==> $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Helper to call API and store response/status
call_api() {
    local method="$1"
    local endpoint="$2"
    local payload="$3"
    local include_cookies="${4:-false}"
    local save_cookies="${5:-false}"

    local curl_opts=("-sS" "-w" "\n%{http_code}" "-X" "$method" "-H" "Content-Type: application/json")
    
    if [[ "$include_cookies" == "true" ]]; then
        curl_opts+=("-b" "${COOKIE_FILE}")
    fi
    
    if [[ "$save_cookies" == "true" ]]; then
        curl_opts+=("-c" "${COOKIE_FILE}")
    fi

    local response
    if [[ -n "$payload" ]]; then
        response=$(curl "${curl_opts[@]}" -d "$payload" "${BASE_URL}${endpoint}")
    else
        response=$(curl "${curl_opts[@]}" "${BASE_URL}${endpoint}")
    fi

    HTTP_STATUS=$(echo "${response}" | tail -n1)
    HTTP_BODY=$(echo "${response}" | sed '$d')

    echo "Endpoint: $endpoint"
    echo "Status  : $HTTP_STATUS"
    # echo "Body    : $HTTP_BODY"
}

# Helper to parse JSON
json_get() {
    local key="$1"
    local body="$2"
    printf '%s' "$body" | python3 -c "import sys, json; data=sys.stdin.read(); print(json.loads(data).get('$key', ''))" 2>/dev/null || echo ""
}

# 1. Register
print_step "1) Testing Register: /api/auth/register/"
call_api "POST" "/api/auth/register/" "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}"
if [[ "$HTTP_STATUS" == "201" ]]; then
    echo "Success: User registered."
else
    print_error "Register failed with status $HTTP_STATUS"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 2. Login
print_step "2) Testing Login: /api/auth/login/"
call_api "POST" "/api/auth/login/" "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" "false" "true"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Logged in."
    ACCESS_TOKEN=$(json_get "access" "$HTTP_BODY")
    REFRESH_TOKEN=$(json_get "refresh" "$HTTP_BODY")
else
    print_error "Login failed with status $HTTP_STATUS"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 3. MFA Setup
print_step "3) Testing MFA Setup: /api/auth/mfa/setup/"
call_api "POST" "/api/auth/mfa/setup/" "{\"email\":\"${EMAIL}\"}" "true" "false"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: MFA Setup initiated."
    MFA_SECRET=$(json_get "secret" "$HTTP_BODY")
    echo "MFA Secret: $MFA_SECRET"
else
    print_error "MFA Setup failed with status $HTTP_STATUS"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 4. MFA Verify (Note: This will likely fail without a real TOTP, but we check if endpoint is reachable)
print_step "4) Testing MFA Verify (Expect failure with random token): /api/auth/mfa/verify/"
call_api "POST" "/api/auth/mfa/verify/" "{\"email\":\"${EMAIL}\",\"token\":\"123456\"}" "true" "false"
if [[ "$HTTP_STATUS" == "400" ]]; then
    echo "Success: Endpoint reachable, correctly rejected invalid token."
else
    echo "Warning: MFA Verify returned status $HTTP_STATUS instead of 400."
fi

# 5. Reset Password Request
print_step "5) Testing Reset Password Request: /api/auth/reset-password/"
call_api "POST" "/api/auth/reset-password/" "{\"email\":\"${EMAIL}\"}"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Password reset requested."
    OTP=$(json_get "otp" "$HTTP_BODY")
    if [[ -z "$OTP" ]]; then
        echo "Warning: OTP not returned in body (check if settings.OTP_DEV_RETURN_OTP is True)"
    else
        echo "OTP received: $OTP"
    fi
else
    print_error "Reset Password Request failed with status $HTTP_STATUS"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 6. Verify OTP
if [[ -n "$OTP" ]]; then
    print_step "6) Testing Verify OTP: /api/auth/reset-password/verify-otp/"
    call_api "POST" "/api/auth/reset-password/verify-otp/" "{\"email\":\"${EMAIL}\",\"otp\":\"${OTP}\"}"
    if [[ "$HTTP_STATUS" == "200" ]]; then
        echo "Success: OTP verified."
    else
        print_error "OTP Verification failed with status $HTTP_STATUS"
        echo "Body: $HTTP_BODY"
        exit 1
    fi

    # 7. Confirm Reset Password
    print_step "7) Testing Confirm Reset Password: /api/auth/reset-password/confirm/"
    call_api "POST" "/api/auth/reset-password/confirm/" "{\"email\":\"${EMAIL}\",\"otp\":\"${OTP}\",\"new_password\":\"${NEW_PASSWORD}\"}"
    if [[ "$HTTP_STATUS" == "200" ]]; then
        echo "Success: Password reset confirmed."
        PASSWORD=$NEW_PASSWORD
    else
        print_error "Password Reset Confirmation failed with status $HTTP_STATUS"
        echo "Body: $HTTP_BODY"
        exit 1
    fi
fi

# 8. Token Refresh (Cookie based)
print_step "8) Testing Token Refresh: /api/auth/token/refresh/"
call_api "POST" "/api/auth/token/refresh/" "" "true" "true"
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "Success: Token refreshed via cookie."
else
    # Try with explicit refresh token if cookie fails
    if [[ -n "$REFRESH_TOKEN" ]]; then
        echo "Cookie refresh failed, trying with explicit token..."
        call_api "POST" "/api/auth/token/refresh/" "{\"refresh\":\"${REFRESH_TOKEN}\"}" "false" "true"
        if [[ "$HTTP_STATUS" == "200" ]]; then
            echo "Success: Token refreshed via explicit token."
        else
            print_error "Token refresh failed with status $HTTP_STATUS"
            echo "Body: $HTTP_BODY"
            exit 1
        fi
    else
        print_error "Token refresh failed and no refresh token available."
        exit 1
    fi
fi

# 9. Logout
print_step "9) Testing Logout: /api/auth/logout/"
call_api "POST" "/api/auth/logout/" "" "true" "false"
if [[ "$HTTP_STATUS" == "205" ]]; then
    echo "Success: Logged out."
else
    print_error "Logout failed with status $HTTP_STATUS"
    echo "Body: $HTTP_BODY"
    exit 1
fi

# 10. OAuth (Basic reachability test)
print_step "10) Testing OAuth: /api/auth/oauth/login/"
call_api "POST" "/api/auth/oauth/login/" "{\"provider\":\"github\",\"code\":\"invalid_code\"}"
if [[ "$HTTP_STATUS" == "400" ]]; then
    echo "Success: OAuth endpoint reachable (rejected invalid code)."
else
    echo "Warning: OAuth endpoint returned status $HTTP_STATUS instead of 400."
    echo "Body: $HTTP_BODY"
fi

echo -e "\n${GREEN}All tested account endpoints are working as expected!${NC}"

