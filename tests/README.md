# Backend tests (pytest + DRF test client)

Quick guide to run the example tests included here.

Setup (recommended):

```
cd PM-A-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-django djangorestframework
```

Run tests:

```
pytest -q
```

Notes:
- The example test posts to `/api/projects/`. If your API prefix differs, update `tests/test_projects_api.py` to the correct URL.
- The tests use Django test database; ensure `DJANGO_SETTINGS_MODULE` is set in `pytest.ini` (already added).
- For manual API debugging, you can use curl (example below).

Example curl to create a project (adjust auth/cookie handling as needed):

```
curl -X POST http://127.0.0.1:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Curl Project","summary":"created with curl","visibility":"private"}' \
  -b "sessionid=YOUR_SESSION_COOKIE"
```
