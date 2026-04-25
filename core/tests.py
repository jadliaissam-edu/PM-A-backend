from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import NotificationEvent
import uuid

# Create your tests here.

class NotificationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email="test@example.com", password="testpass123")
        self.client.force_authenticate(self.user)
        NotificationEvent.objects.create(
            project_id=uuid.uuid4(),
            user=self.user,
            event_type="mention",
            payload_json={"message": "Test notification"}
        )

    def test_list_user_notifications(self):
        url = "/api/core/notifications/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]["event_type"], "mention")
