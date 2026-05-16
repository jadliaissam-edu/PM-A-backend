# PM-A-backend

## API Reference

See [API_REFERENCE.md](API_REFERENCE.md) for request and response examples for the current backend endpoints.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py runserver
```


API base (frontend → backend): NEXT_PUBLIC_API_URL → e.g. http://backend:8000
Frontend public automation URL (frontend → n8n): NEXT_PUBLIC_N8N_URL → e.g. http://n8n:5678
Login / Auth: frontend calls backend login endpoint to obtain JWT; store token (secure cookie or memory) and send Authorization: Bearer <JWT> on protected requests.
Token refresh: support refresh endpoint or refresh flow (refresh token storage + renew access token).
Ticket creation (preferred flow): frontend POST → n8n webhook (${NEXT_PUBLIC_N8N_URL}/webhook/<webhookId>/ticket) with payload containing project_id, title, description, tag.
Ticket creation (direct alternative): frontend POST → POST /api/projects/{project_id}/tickets/ with Authorization header and JSON body.
n8n → backend auth: n8n must send Authorization: Bearer <BACKEND_JWT> (store as n8n Credential or BACKEND_JWT env). Prefer n8n Credentials.
n8n env/credentials: provide BACKEND_URL and BACKEND_JWT to n8n (use Credentials for secret JWT). If using env expressions, ensure N8N_BLOCK_ENV_ACCESS_IN_NODE=false (dev only).
CORS & CSRF (backend): add django-cors-headers and set CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS to frontend origin(s) (or enable CORS_ALLOW_ALL_ORIGINS=true in dev).
Allowed hosts & secrets (backend): configure ALLOWED_HOSTS, DJANGO_SECRET_KEY, DB credentials in env or secret store.
Public envs at build time: pass NEXT_PUBLIC_API_URL and NEXT_PUBLIC_N8N_URL into the frontend build (or provide at runtime if using runtime env injection).
Docker networking: reference services by name inside compose (backend:8000, n8n:5678); expose host ports as needed (3000, 8000, 5678). Use env_file in docker-compose.yml.
DB & migrations: run python manage.py migrate (or run migrations on container start) and ensure DB credentials/volumes are configured.
Static / media storage: mount volumes for STATIC_ROOT/MEDIA_ROOT or configure external storage.
Health & readiness: add health endpoint for backend and check it from orchestration/monitoring.
Logging / errors: ensure backend logs are writable and accessible; make n8n logs accessible (~/.n8n volume).
Security best-practices: use HTTPS for production, pin images/versions, prefer n8n Credentials over env-based secrets, do not expose JWTs in client-side code.
Optional extras: WebSocket/notifications endpoint, rate-limiting, service account JWT for n8n if you need non-user-scoped access.
