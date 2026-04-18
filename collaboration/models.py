from django.db import models

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

import uuid
from django.db import models


class CommentMention(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    comment = models.ForeignKey(
        'collaboration.Comment',
        on_delete=models.CASCADE,
        related_name='mentions'
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='mentioned_in_comments'
    )

    class Meta:
        unique_together = ('comment', 'user')

class ReactionType(models.TextChoices):
    LIKE = "like", "Like"
    LOVE = "love", "Love"
    LAUGH = "laugh", "Laugh"
    EYES = "eyes", "Eyes"
    ROCKET = "rocket", "Rocket"
class Reaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    comment = models.ForeignKey(
        'collaboration.Comment',
        on_delete=models.CASCADE,
        related_name='reactions'
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reactions'
    )

    reaction_type = models.CharField(
        max_length=20,
        choices=ReactionType.choices
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user', 'reaction_type')