import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.serializer import EmailTokenObtainPairSerializer
try:
    EmailTokenObtainPairSerializer().validate({"email": "123@123.com", "password": "string"})
except Exception as e:
    import traceback
    traceback.print_exc()

