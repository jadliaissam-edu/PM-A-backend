from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings
from django.core.validators import FileExtensionValidator

# Commenting out the unused custom User model to avoid confusion with django.contrib.auth.models.User
# which is currently set as AUTH_USER_MODEL in settings.py.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
"""

class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    # FileField/ImageField stored via configured storage backend (MinIO/S3)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)
    preferences_json = models.JSONField(default=dict)

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() >= self.expires_at

class MFAConfig(models.Model):
    METHOD_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('authenticator', 'Authenticator App'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mfa_config')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    secret = models.CharField(max_length=255, blank=True, null=True)
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class OAuthProvider(models.TextChoices):
    GITHUB = "github", "GitHub"
    GOOGLE = "google", "Google"

class OAuthAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='oauth_accounts')
    provider = models.CharField(max_length=50, choices=OAuthProvider.choices)
    provider_user_id = models.CharField(max_length=255)