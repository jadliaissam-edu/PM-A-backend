from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from django.conf import settings

from .models import Organization, Workspace


class WorkspaceCookieAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cookie-user",
            email="cookie@example.com",
            password="secret123",
        )
        self.organization = Organization.objects.create(name="Matier")
        self.workspace = Workspace.objects.create(
            organization=self.organization,
            name="Enterprise",
            visibility="internal",
        )

    def test_workspaces_endpoint_accepts_access_cookie(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "cookie@example.com", "password": "secret123"},
            format="json",
        )

        self.client.cookies[settings.JWT_ACCESS_COOKIE] = login_response.cookies[
            settings.JWT_ACCESS_COOKIE
        ].value

        response = self.client.get("/api/orgs/workspaces/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "Enterprise")
