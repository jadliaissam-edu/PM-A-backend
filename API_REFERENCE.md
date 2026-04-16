# PM-A Backend API Reference

Base URL:

```text
http://127.0.0.1:8000
```

## Health Check

### GET `/api/health/`

Request:

```bash
curl -i http://127.0.0.1:8000/api/health/
```

Response `200 OK`:

```json
{
  "status": "ok"
}
```

## Authentication

### POST `/api/auth/register/`

Create a new user.

Request:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"username":"hassine1","email":"hassinetrigui5@gmail.com","password":"StrongPass123!"}'
```

Request body:

```json
{
  "username": "hassine1",
  "email": "hassinetrigui5@gmail.com",
  "password": "StrongPass123!"
}
```

Response `201 Created`:

```json
{
  "id": 1,
  "username": "hassine1",
  "email": "hassinetrigui5@gmail.com"
}
```

### POST `/api/auth/login/`

Obtain JWT tokens.

Request:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"hassine1","password":"StrongPass123!"}'
```

Request body:

```json
{
  "username": "hassine1",
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

Refresh an access token.

Request:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh-token>"}'
```

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

## Password Reset

### POST `/api/auth/reset-password/`

Request an OTP for password reset.

Request:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/auth/reset-password/" \
  -H "Content-Type: application/json" \
  -d '{"email":"hassinetrigui5@gmail.com"}'
```

Request body:

```json
{
  "email": "hassinetrigui5@gmail.com"
}
```

Response `200 OK` when user exists and email is sent:

```json
{
  "email": "hassinetrigui5@gmail.com",
  "message": "OTP generated successfully and sent to email.",
  "expires_in_minutes": 10
}
```

Response `200 OK` in dev fallback mode when SMTP fails:

```json
{
  "email": "hassinetrigui5@gmail.com",
  "message": "OTP generated, but email sending failed. Using dev OTP response.",
  "expires_in_minutes": 10,
  "otp": "123456"
}
```

Response `200 OK` when the email does not match a user:

```json
{
  "email": "hassinetrigui5@gmail.com",
  "message": "If the email exists, an OTP has been generated."
}
```

### POST `/api/auth/reset-password/verify-otp/`

Verify the OTP before changing the password.

Request:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/auth/reset-password/verify-otp/" \
  -H "Content-Type: application/json" \
  -d '{"email":"hassinetrigui5@gmail.com","otp":"123456"}'
```

Request body:

```json
{
  "email": "hassinetrigui5@gmail.com",
  "otp": "123456"
}
```

Response `200 OK`:

```json
{
  "message": "OTP is valid."
}
```

Response `400 Bad Request`:

```json
{
  "error": "Invalid or expired OTP."
}
```

### POST `/api/auth/reset-password/confirm/`

Confirm the password reset using email, OTP, and new password.

Request:

```bash
curl -i -X POST "http://127.0.0.1:8000/api/auth/reset-password/confirm/" \
  -H "Content-Type: application/json" \
  -d '{"email":"hassinetrigui5@gmail.com","otp":"123456","new_password":"NewStrongPass123!"}'
```

Request body:

```json
{
  "email": "hassinetrigui5@gmail.com",
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

## Response Notes

- `OTP_DEV_RETURN_OTP=True` includes the OTP in the reset-password response for development.
- `OTP_DEV_RETURN_OTP=False` sends the OTP only by email.
- Email delivery depends on valid SMTP settings in `.env`.
- All password reset endpoints use `application/json` request bodies.
