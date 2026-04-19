
from django.db import models
from django.utils import timezone
import uuid

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
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

class PasswordResetOTP(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
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
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mfa_config')
	method = models.CharField(max_length=20, choices=METHOD_CHOICES)
	secret = models.CharField(max_length=255, blank=True, null=True)
	is_enabled = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)


# Backward-compatible alias for existing imports/usages.
MFaConfig = MFAConfig

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user