import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_create_project_api():
    """Basic DRF test: create a project via the API.

    Adjust the URL if your API prefix differs (e.g. /api/projects/ vs /projects/).
    """
    client = APIClient()
    User = get_user_model()
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_authenticate(user=user)

    payload = {"name": "Test Project", "summary": "Created by test", "visibility": "private"}
    # Most deployments expose projects under /api/projects/ or /projects/. Update if needed.
    resp = client.post("/api/projects/", payload, format="json")

    assert resp.status_code in (200, 201), f"Unexpected status: {resp.status_code} - {resp.content}"
    data = resp.json()
    assert data.get("name") == "Test Project"
