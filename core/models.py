import uuid
from django.db import models
from django.conf import settings

class NotificationChannel(models.TextChoices):
    WEBSOCKET = "websocket", "WebSocket"

class NotificationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_id = models.UUIDField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    event_type = models.CharField(max_length=255)
    payload_json = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class UserAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=255)
    target_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)



class Dashboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard')


class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    project_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'project_id'),)
