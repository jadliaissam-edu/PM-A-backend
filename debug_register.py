import os, json, sys, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.test import RequestFactory
from accounts.views import RegisterView
factory = RequestFactory()
request = factory.post(
    '/api/auth/register/', 
    data=json.dumps({'username':'gezrrezr1', 'email':'user1@example.com', 'password':'password'}),
    content_type='application/json'
)
try:
    response = RegisterView.as_view()(request)
    print("STATUS:", response.status_code)
    print("CONTENT:", response.content)
except Exception as e:
    traceback.print_exc()
