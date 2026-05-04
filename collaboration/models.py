import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    mentions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ReactionType(models.TextChoices):
    LIKE = "like", "Like"
    LOVE = "love", "Love"
    LAUGH = "laugh", "Laugh"
    EYES = "eyes", "Eyes"
    ROCKET = "rocket", "Rocket"

class Reaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reactions')
    type = models.CharField(max_length=50, choices=ReactionType.choices, default=ReactionType.LIKE)
    created_at = models.DateTimeField(auto_now_add=True)


class ChatChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('orgs.Workspace', on_delete=models.CASCADE, related_name='channels', null=True, blank=True)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, related_name='channels', null=True, blank=True)
    
    is_direct = models.BooleanField(default=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_channels', blank=True)

    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ctx = self.project.name if self.project else (self.workspace.name if self.workspace else "DM")
        return f"#{self.name} ({ctx})"


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    content = models.TextField()
    is_direct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        dest = self.channel.name if self.channel else (self.receiver.username if self.receiver else "Unknown")
        return f"From {self.sender.username} to {dest}: {self.content[:20]}..."