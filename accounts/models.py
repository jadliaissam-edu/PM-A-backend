from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import uuid

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

