from django.test import TestCase
from django.contrib.auth.models import User 

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')

    def test_login(self):
        response = self.client.post('/api/login/', {'username': 'testuser', 'password': 'testpass'}) 
        self.assertEqual(response.status_code, 200) 

