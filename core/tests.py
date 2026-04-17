from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CurrentUserProfileViewTests(APITestCase):
	def setUp(self):
		self.url = reverse("current-user-profile")
		self.user = get_user_model().objects.create_user(
			username="me_user",
			email="me@example.com",
			password="StrongPass123!",
			first_name="Me",
			last_name="User",
		)

	def test_get_profile_requires_authentication(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_profile_returns_authenticated_user_data(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["id"], self.user.id)
		self.assertEqual(response.data["username"], self.user.username)
		self.assertEqual(response.data["email"], self.user.email)
		self.assertEqual(response.data["first_name"], self.user.first_name)
		self.assertEqual(response.data["last_name"], self.user.last_name)

	def test_patch_profile_requires_authentication(self):
		response = self.client.patch(
			self.url,
			{"first_name": "Updated"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_patch_profile_updates_first_and_last_name(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.patch(
			self.url,
			{"first_name": "Hassine", "last_name": "Trigui"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["message"], "Profile updated successfully")

		self.user.refresh_from_db()
		self.assertEqual(self.user.first_name, "Hassine")
		self.assertEqual(self.user.last_name, "Trigui")
