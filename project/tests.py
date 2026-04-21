from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from orgs.models import Organization, Workspace


class ProjectApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="frontend-user",
            email="frontend@example.com",
            password="secret123",
        )
        token_response = self.client.post(
            "/api/auth/login/",
            {"email": "frontend@example.com", "password": "secret123"},
            format="json",
        )
        self.access_token = token_response.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.organization = Organization.objects.create(name="Matier")
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name="Product",
            visibility="internal",
        )
        self.project_id = None

    def test_create_project_and_dashboard_payload(self):
        create_response = self.client.post(
            "/api/projects/",
            {
                "name": "Frontend Ready Project",
                "description": "Project data for dashboard and profile pages.",
                "workspace_id": str(self.workspace.id),
                "type": "software",
                "visibility": "private",
                "status": "active",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json()["name"], "Frontend Ready Project")
        self.assertEqual(create_response.json()["workspace"]["name"], "Product")
        self.project_id = create_response.json()["id"]

        dashboard_response = self.client.get("/api/dashboard/")
        self.assertEqual(dashboard_response.status_code, 200)
        payload = dashboard_response.json()
        self.assertEqual(payload["summary"]["projects"], 1)
        self.assertEqual(payload["organizations"][0]["workspaces"][0]["projects"][0]["name"], "Frontend Ready Project")

        roles_response = self.client.get(f"/api/projects/{self.project_id}/roles/")
        self.assertEqual(roles_response.status_code, 200)
        self.assertEqual(len(roles_response.json()), 1)

    def test_ticket_and_comment_v4_endpoints(self):
        project_response = self.client.post(
            "/api/projects/",
            {
                "name": "Delivery",
                "description": "",
                "workspace_id": str(self.workspace.id),
            },
            format="json",
        )
        project_id = project_response.json()["id"]

        board_response = self.client.get(f"/api/projects/{project_id}/board/")
        first_column_id = board_response.json()["board"]["columns"][0]["id"]

        ticket_response = self.client.post(
            f"/api/projects/{project_id}/tickets/",
            {
                "title": "Implement login page",
                "description_markdown": "Frontend ticket",
                "current_column": first_column_id,
                "type": "task",
                "priority": "high",
                "status": "todo",
                "labels": ["frontend"],
            },
            format="json",
        )
        self.assertEqual(ticket_response.status_code, 201)
        ticket_id = ticket_response.json()["id"]

        comment_response = self.client.post(
            f"/api/projects/{project_id}/tickets/{ticket_id}/comments/",
            {"body": "Need this before dashboard polish."},
            format="json",
        )
        self.assertEqual(comment_response.status_code, 201)

        release_response = self.client.post(
            f"/api/projects/{project_id}/releases/",
            {"tag": "v1.0.0", "target_date": "2026-05-01", "description": "First release"},
            format="json",
        )
        self.assertEqual(release_response.status_code, 201)

        backlog_response = self.client.post(
            f"/api/projects/{project_id}/backlog/",
            {"ticket_id": ticket_id, "rank": 1, "priority_score": 100},
            format="json",
        )
        self.assertEqual(backlog_response.status_code, 201)

    def test_profile_endpoint_returns_authenticated_user(self):
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "frontend@example.com")
