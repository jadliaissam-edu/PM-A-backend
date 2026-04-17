# PM-A Backend API Reference

Base URL:

```text
http://127.0.0.1:8000
```

All request/response examples use JSON.

## Authentication Headers

Use JWT access token for protected endpoints:

```http
Authorization: Bearer <access-token>
```

## Health

### GET `/api/health/`

Response `200 OK`:

```json
{
  "status": "ok"
}
```

## Auth And Account

### POST `/api/auth/register/`

Create user account.

Request body:

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "StrongPass123!"
}
```

Response `201 Created`:

```json
{
  "username": "testuser",
  "email": "test@example.com"
}
```

### POST `/api/auth/login/`

Get JWT tokens.

Request body:

```json
{
  "username": "testuser",
  "password": "StrongPass123!"
}
```

Response `200 OK`:

```json
{
  "refresh": "<refresh-token>",
  "access": "<access-token>"
}
```

### POST `/api/auth/token/refresh/`

Refresh JWT access token.

Request body:

```json
{
  "refresh": "<refresh-token>"
}
```

Response `200 OK`:

```json
{
  "access": "<new-access-token>"
}
```

### POST `/api/auth/mfa/setup/`

Setup MFA authenticator secret and QR URL.

Request body:

```json
{
  "email": "test@example.com"
}
```

Response `200 OK`:

```json
{
  "email": "test@example.com",
  "method": "authenticator",
  "is_enabled": false,
  "qr_url": "otpauth://totp/...",
  "secret": "BASE32SECRET"
}
```

Common error responses:

```json
{
  "error": "User not found."
}
```

### POST `/api/auth/mfa/verify/`

Verify MFA token and enable MFA.

Request body:

```json
{
  "email": "test@example.com",
  "token": "123456"
}
```

Response `200 OK`:

```json
{
  "message": "MFA verified and enabled."
}
```

Common error responses:

```json
{
  "error": "Invalid MFA token."
}
```

### POST `/api/auth/reset-password/`

Generate password reset OTP.

Request body:

```json
{
  "email": "test@example.com"
}
```

Response `200 OK` (email sent):

```json
{
  "email": "test@example.com",
  "message": "OTP generated successfully and sent to email.",
  "expires_in_minutes": 10
}
```

Response `200 OK` (dev fallback):

```json
{
  "email": "test@example.com",
  "message": "OTP generated, but email sending failed. Using dev OTP response.",
  "expires_in_minutes": 10,
  "otp": "123456"
}
```

Response `200 OK` (unknown email, hidden user existence):

```json
{
  "email": "test@example.com",
  "message": "If the email exists, an OTP has been generated."
}
```

### POST `/api/auth/reset-password/verify-otp/`

Verify OTP before password change.

Request body:

```json
{
  "email": "test@example.com",
  "otp": "123456"
}
```

Response `200 OK`:

```json
{
  "message": "OTP is valid."
}
```

Error `400 Bad Request`:

```json
{
  "error": "Invalid or expired OTP."
}
```

### POST `/api/auth/reset-password/confirm/`

Reset password using OTP.

Request body:

```json
{
  "email": "test@example.com",
  "otp": "123456",
  "new_password": "NewStrongPass123!"
}
```

Response `200 OK`:

```json
{
  "message": "Password reset successful."
}
```

## Legacy Auth Endpoints

These are available for backward compatibility and map to SimpleJWT.

### POST `/api/login/`

Request body:

```json
{
  "username": "testuser",
  "password": "StrongPass123!"
}
```

Response `200 OK`:

```json
{
  "refresh": "<refresh-token>",
  "access": "<access-token>"
}
```

### POST `/api/token/refresh/`

Request body:

```json
{
  "refresh": "<refresh-token>"
}
```

Response `200 OK`:

```json
{
  "access": "<new-access-token>"
}
```

### POST `/api/token/verify/`

Request body:

```json
{
  "token": "<access-or-refresh-token>"
}
```

Response `200 OK`:

```json
{}
```

## Users

All endpoints below require JWT authentication.

### GET `/api/users/me/`

Response `200 OK`:

```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User"
}
```

### PATCH `/api/users/me/`

Request body (all fields optional):

```json
{
  "username": "newname",
  "email": "new@example.com",
  "first_name": "New",
  "last_name": "Name"
}
```

Response `200 OK`:

```json
{
  "message": "Profile updated successfully"
}
```

### GET `/api/users/<user_id>/`

Response `200 OK`:

```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User"
}
```

Error `404 Not Found`:

```json
{
  "error": "User not found"
}
```

## Dashboard

All endpoints below require JWT authentication.

### GET `/api/dashboard/`

Response `200 OK`:

```json
{
  "total_projects": 5,
  "owned_projects": 2,
  "member_projects": 3,
  "archived_projects": 1,
  "recent_projects": [
    {
      "id": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
      "name": "Alpha",
      "description": "Project description",
      "owner": 1,
      "owner_username": "testuser",
      "is_archived": false,
      "is_closed": false,
      "created_at": "2026-04-17T10:30:00Z"
    }
  ]
}
```

### GET `/api/dashboard/stats/`

Response shape is the same as `/api/dashboard/`.

### GET `/api/dashboard/recent-projects/`

Response `200 OK`:

```json
[
  {
    "id": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
    "name": "Alpha",
    "description": "Project description",
    "owner": 1,
    "owner_username": "testuser",
    "is_archived": false,
    "is_closed": false,
    "created_at": "2026-04-17T10:30:00Z"
  }
]
```

## Projects

All endpoints below require JWT authentication.

### GET `/api/projects/`

List projects where current user is owner/member.

Response `200 OK`:

```json
[
  {
    "id": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
    "name": "Alpha",
    "description": "Project description",
    "owner": 1,
    "owner_username": "testuser",
    "is_archived": false,
    "is_closed": false,
    "created_at": "2026-04-17T10:30:00Z"
  }
]
```

### POST `/api/projects/`

Create project.

Request body:

```json
{
  "name": "Alpha",
  "description": "Project description",
  "is_archived": false,
  "is_closed": false
}
```

Response `201 Created`:

```json
{
  "id": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
  "name": "Alpha",
  "description": "Project description",
  "owner": 1,
  "owner_username": "testuser",
  "is_archived": false,
  "is_closed": false,
  "created_at": "2026-04-17T10:30:00Z"
}
```

### GET `/api/projects/<project_id>/`

Get one project.

Response `200 OK`: same project object as above.

Error `404 Not Found`:

```json
{
  "error": "Project not found."
}
```

### PATCH `/api/projects/<project_id>/`

Update project (owner only).

Request body (partial):

```json
{
  "name": "Alpha Updated",
  "description": "Updated description",
  "is_archived": false,
  "is_closed": false
}
```

Response `200 OK`: updated project object.

Error `403 Forbidden`:

```json
{
  "error": "Only the owner can update this project."
}
```

### DELETE `/api/projects/<project_id>/`

Delete project (owner only).

Response `204 No Content`.

Error `403 Forbidden`:

```json
{
  "error": "Only the owner can delete this project."
}
```

### POST `/api/projects/<project_id>/archive/`

Archive project (owner only).

Response `200 OK`:

```json
{
  "message": "Project archived."
}
```

### POST `/api/projects/<project_id>/close/`

Close project (owner only).

Response `200 OK`:

```json
{
  "message": "Project closed."
}
```

### GET `/api/projects/<project_id>/members/`

Get project members with roles.

Response `200 OK`:

```json
{
  "project_id": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
  "members": [
    {
      "id": 1,
      "username": "owner",
      "email": "owner@example.com",
      "role": "owner"
    },
    {
      "id": 2,
      "username": "devuser",
      "email": "dev@example.com",
      "role": "dev"
    }
  ]
}
```

## Board

All endpoints below require JWT authentication.

### GET `/api/projects/<project_id>/board/`

Get project board and columns.

Response `200 OK`:

```json
{
  "project_id": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
  "board_id": "0c80354b-4d4e-4e4f-95f2-39fcd89a9c8f",
  "columns": [
    {
      "id": "f8bcc2e0-7f91-4cbe-97f3-aac15a3e23df",
      "board": "0c80354b-4d4e-4e4f-95f2-39fcd89a9c8f",
      "name": "To Do",
      "position": 0
    }
  ]
}
```

### POST `/api/projects/<project_id>/board/columns/`

Create board column (owner only).

Request body:

```json
{
  "name": "In Progress",
  "position": 1
}
```

Response `201 Created`:

```json
{
  "id": "f8bcc2e0-7f91-4cbe-97f3-aac15a3e23df",
  "board": "0c80354b-4d4e-4e4f-95f2-39fcd89a9c8f",
  "name": "In Progress",
  "position": 1
}
```

### PATCH `/api/board/columns/<column_id>/`

Update board column (owner only).

Request body:

```json
{
  "name": "Done",
  "position": 2
}
```

Response `200 OK`:

```json
{
  "id": "f8bcc2e0-7f91-4cbe-97f3-aac15a3e23df",
  "board": "0c80354b-4d4e-4e4f-95f2-39fcd89a9c8f",
  "name": "Done",
  "position": 2
}
```

### DELETE `/api/board/columns/<column_id>/`

Delete board column (owner only).

Response `204 No Content`.

## Roles

All endpoints below require JWT authentication.

Role enum values:

- `chef_de_project`
- `admin`
- `dev`
- `observer`

### GET `/api/projects/<project_id>/roles/`

List project roles.

Response `200 OK`:

```json
[
  {
    "id": "2f4dc8b5-f757-4cb4-a0d9-ecfbdb14f815",
    "project": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
    "user": 2,
    "user_username": "devuser",
    "role_name": "dev",
    "permissions": [],
    "created_at": "2026-04-17T10:40:00Z"
  }
]
```

### POST `/api/projects/<project_id>/roles/`

Assign role (owner only).

Request body:

```json
{
  "user": 2,
  "role_name": "dev",
  "permissions": ["task.read", "task.update"]
}
```

Response `201 Created`:

```json
{
  "id": "2f4dc8b5-f757-4cb4-a0d9-ecfbdb14f815",
  "project": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
  "user": 2,
  "user_username": "devuser",
  "role_name": "dev",
  "permissions": ["task.read", "task.update"],
  "created_at": "2026-04-17T10:40:00Z"
}
```

### PATCH `/api/projects/<project_id>/roles/<role_id>/`

Update role (owner only).

Request body (partial):

```json
{
  "role_name": "admin",
  "permissions": ["*"]
}
```

Response `200 OK`:

```json
{
  "id": "2f4dc8b5-f757-4cb4-a0d9-ecfbdb14f815",
  "project": "9a0f1ff7-6a8f-4fd6-9ef5-8f698fb64830",
  "user": 2,
  "user_username": "devuser",
  "role_name": "admin",
  "permissions": ["*"],
  "created_at": "2026-04-17T10:40:00Z"
}
```

### DELETE `/api/projects/<project_id>/roles/<role_id>/`

Revoke role (owner only).

Response `204 No Content`.

## Common Error Responses

### Unauthorized `401`

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Forbidden `403`

```json
{
  "error": "Only the owner can assign roles."
}
```

### Validation error `400`

```json
{
  "field_name": ["Error message"]
}
```

## Notes

- `OTP_DEV_RETURN_OTP=True` can include OTP in reset response for development.
- Production should disable `OTP_DEV_RETURN_OTP` and configure SMTP.

## Curl Test Commands

Use this section to test all endpoints quickly.

### 1. Setup Variables

```bash
BASE_URL="http://127.0.0.1:8000"
USERNAME="testuser"
EMAIL="test@example.com"
PASSWORD="StrongPass123!"
NEW_PASSWORD="NewStrongPass123!"
TOKEN=""
REFRESH=""
PROJECT_ID=""
COLUMN_ID=""
ROLE_ID=""
TARGET_USER_ID="2"
OTP_CODE="123456"
MFA_TOKEN="123456"
```

### 2. Public Endpoints

```bash
# Health
curl -i "$BASE_URL/api/health/"

# Register
curl -i -X POST "$BASE_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"

# Login (auth endpoint)
curl -i -X POST "$BASE_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}"

# Login (legacy endpoint)
curl -i -X POST "$BASE_URL/api/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}"
```

### 3. Capture JWT Tokens

```bash
LOGIN_JSON=$(curl -s -X POST "$BASE_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_JSON" | sed -n 's/.*"access":"\([^"]*\)".*/\1/p')
REFRESH=$(echo "$LOGIN_JSON" | sed -n 's/.*"refresh":"\([^"]*\)".*/\1/p')

echo "TOKEN=$TOKEN"
echo "REFRESH=$REFRESH"
```

### 4. Token Refresh/Verify

```bash
# Refresh (auth endpoint)
curl -i -X POST "$BASE_URL/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"

# Refresh (legacy endpoint)
curl -i -X POST "$BASE_URL/api/token/refresh/" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"

# Verify (legacy endpoint)
curl -i -X POST "$BASE_URL/api/token/verify/" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN\"}"
```

### 5. Password Reset + MFA

```bash
# Request reset OTP
curl -i -X POST "$BASE_URL/api/auth/reset-password/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}"

# Verify reset OTP
curl -i -X POST "$BASE_URL/api/auth/reset-password/verify-otp/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"otp\":\"$OTP_CODE\"}"

# Confirm reset OTP
curl -i -X POST "$BASE_URL/api/auth/reset-password/confirm/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"otp\":\"$OTP_CODE\",\"new_password\":\"$NEW_PASSWORD\"}"

# MFA setup
curl -i -X POST "$BASE_URL/api/auth/mfa/setup/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}"

# MFA verify
curl -i -X POST "$BASE_URL/api/auth/mfa/verify/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"token\":\"$MFA_TOKEN\"}"
```

### 6. Authenticated User Endpoints

```bash
# Current user profile
curl -i "$BASE_URL/api/users/me/" \
  -H "Authorization: Bearer $TOKEN"

# Update current profile
curl -i -X PATCH "$BASE_URL/api/users/me/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User"}'

# User detail
curl -i "$BASE_URL/api/users/1/" \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Dashboard Endpoints

```bash
curl -i "$BASE_URL/api/dashboard/" \
  -H "Authorization: Bearer $TOKEN"

curl -i "$BASE_URL/api/dashboard/stats/" \
  -H "Authorization: Bearer $TOKEN"

curl -i "$BASE_URL/api/dashboard/recent-projects/" \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Project Endpoints

```bash
# Create project
PROJECT_JSON=$(curl -s -X POST "$BASE_URL/api/projects/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alpha","description":"Project description","is_archived":false,"is_closed":false}')

echo "$PROJECT_JSON"
PROJECT_ID=$(echo "$PROJECT_JSON" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo "PROJECT_ID=$PROJECT_ID"

# List projects
curl -i "$BASE_URL/api/projects/" \
  -H "Authorization: Bearer $TOKEN"

# Get project
curl -i "$BASE_URL/api/projects/$PROJECT_ID/" \
  -H "Authorization: Bearer $TOKEN"

# Update project
curl -i -X PATCH "$BASE_URL/api/projects/$PROJECT_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alpha Updated","description":"Updated description"}'

# Archive project
curl -i -X POST "$BASE_URL/api/projects/$PROJECT_ID/archive/" \
  -H "Authorization: Bearer $TOKEN"

# Close project
curl -i -X POST "$BASE_URL/api/projects/$PROJECT_ID/close/" \
  -H "Authorization: Bearer $TOKEN"

# Project members
curl -i "$BASE_URL/api/projects/$PROJECT_ID/members/" \
  -H "Authorization: Bearer $TOKEN"
```

### 9. Board Endpoints

```bash
# Get board
curl -i "$BASE_URL/api/projects/$PROJECT_ID/board/" \
  -H "Authorization: Bearer $TOKEN"

# Create column
COLUMN_JSON=$(curl -s -X POST "$BASE_URL/api/projects/$PROJECT_ID/board/columns/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"To Do","position":0}')

echo "$COLUMN_JSON"
COLUMN_ID=$(echo "$COLUMN_JSON" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo "COLUMN_ID=$COLUMN_ID"

# Update column
curl -i -X PATCH "$BASE_URL/api/board/columns/$COLUMN_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Done","position":1}'

# Delete column
curl -i -X DELETE "$BASE_URL/api/board/columns/$COLUMN_ID/" \
  -H "Authorization: Bearer $TOKEN"
```

### 10. Role Endpoints

```bash
# Create role assignment
ROLE_JSON=$(curl -s -X POST "$BASE_URL/api/projects/$PROJECT_ID/roles/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"user\":$TARGET_USER_ID,\"role_name\":\"dev\",\"permissions\":[\"task.read\",\"task.update\"]}")

echo "$ROLE_JSON"
ROLE_ID=$(echo "$ROLE_JSON" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo "ROLE_ID=$ROLE_ID"

# List roles
curl -i "$BASE_URL/api/projects/$PROJECT_ID/roles/" \
  -H "Authorization: Bearer $TOKEN"

# Update role
curl -i -X PATCH "$BASE_URL/api/projects/$PROJECT_ID/roles/$ROLE_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_name":"admin","permissions":["*"]}'

# Delete role
curl -i -X DELETE "$BASE_URL/api/projects/$PROJECT_ID/roles/$ROLE_ID/" \
  -H "Authorization: Bearer $TOKEN"
```

### 11. Optional Cleanup

```bash
curl -i -X DELETE "$BASE_URL/api/projects/$PROJECT_ID/" \
  -H "Authorization: Bearer $TOKEN"
```
