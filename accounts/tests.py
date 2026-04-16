from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import PasswordResetOTP


class RegisterViewTest(APITestCase):
    def test_register_creates_user(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertNotIn('password', response.data)


class PasswordResetRequestViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )

    @override_settings(OTP_DEV_RETURN_OTP=True)
    @patch('accounts.views.send_mail', return_value=1)
    def test_reset_password_creates_otp(self, mocked_send_mail):
        response = self.client.post(
            '/api/auth/reset-password/',
            {'email': 'test@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('message', response.data)
        self.assertIn('otp', response.data)
        self.assertTrue(
            PasswordResetOTP.objects.filter(
                user=self.user,
                otp_code=response.data['otp'],
                is_used=False,
            ).exists()
        )
        mocked_send_mail.assert_called_once()

    @override_settings(OTP_DEV_RETURN_OTP=True)
    @patch('accounts.views.send_mail', side_effect=Exception('smtp failed'))
    def test_reset_password_returns_otp_when_email_send_fails_in_dev(self, mocked_send_mail):
        response = self.client.post(
            '/api/auth/reset-password/',
            {'email': 'test@example.com'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('otp', response.data)
        self.assertIn('message', response.data)
        self.assertTrue(
            PasswordResetOTP.objects.filter(
                user=self.user,
                otp_code=response.data['otp'],
                is_used=False,
            ).exists()
        )
        mocked_send_mail.assert_called_once()

