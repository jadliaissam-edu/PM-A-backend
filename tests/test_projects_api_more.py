import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_projects_list_requires_auth():
    client = APIClient()
    resp = client.get("/api/projects/")
    assert resp.status_code in (401, 403, 302), "Unauthenticated request should be rejected"


@pytest.mark.django_db
def test_create_and_get_project():
    client = APIClient()
    User = get_user_model()
    user = User.objects.create_user(username="apitestuser", password="testpass")
    client.force_authenticate(user=user)

    payload = {"name": "API Test Project", "summary": "Created by test", "visibility": "private"}
    resp = client.post("/api/projects/", payload, format="json")
    assert resp.status_code in (200, 201), f"Create failed: {resp.status_code} {resp.content}"
    data = resp.json()
    project_id = data.get("id") or data.get("pk")
    assert project_id, "Response did not include project id"

    # Retrieve the created project
    resp2 = client.get(f"/api/projects/{project_id}/")
    assert resp2.status_code == 200, f"GET project failed: {resp2.status_code} {resp2.content}"
    data2 = resp2.json()
    assert data2.get("name") == payload["name"]
