from rest_framework import serializers

from .models import Comment, Reaction


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "ticket",
            "author",
            "author_username",
            "body",
            "mentions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "ticket", "author", "author_username", "created_at", "updated_at"]


class ReactionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "comment", "user", "username", "type", "created_at"]
        read_only_fields = ["id", "comment", "user", "username", "created_at"]
