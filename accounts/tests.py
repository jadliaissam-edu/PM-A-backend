from django.test import TestCase
from django.contrib.auth.models import User 
from django.conf import settings

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')

    def test_login(self):
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'test@example.com', 'password': 'testpass'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200) 
        self.assertIn('access', response.json())
        self.assertEqual(response.json()['email'], 'test@example.com')
        self.assertIn(settings.JWT_REFRESH_COOKIE, response.cookies)

    def test_login_with_duplicate_email_uses_matching_password(self):
        User.objects.create_user(username='seconduser', email='test@example.com', password='otherpass')

        response = self.client.post(
            '/api/auth/login/',
            {'email': 'test@example.com', 'password': 'testpass'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'testuser')

    def test_login_with_duplicate_email_and_ambiguous_password_is_rejected(self):
        User.objects.create_user(username='seconduser', email='test@example.com', password='testpass')

        response = self.client.post(
            '/api/auth/login/',
            {'email': 'test@example.com', 'password': 'testpass'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Multiple accounts use this email', str(response.json()))

    def test_refresh_uses_cookie(self):
        login_response = self.client.post(
            '/api/auth/login/',
            {'email': 'test@example.com', 'password': 'testpass'},
            content_type='application/json',
        )

        refresh_cookie = login_response.cookies[settings.JWT_REFRESH_COOKIE].value
        self.client.cookies[settings.JWT_REFRESH_COOKIE] = refresh_cookie

        response = self.client.post(
            '/api/auth/token/refresh/',
            {},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
