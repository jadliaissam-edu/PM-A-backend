from rest_framework import serializers

from .models import ChatChannel, ChatMessage, Comment, Reaction


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


class ChatChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatChannel
        fields = ["id", "organization", "name", "description", "created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    receiver_username = serializers.CharField(source="receiver.username", read_only=True)
    channel_name = serializers.CharField(source="channel.name", read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "channel",
            "channel_name",
            "sender",
            "sender_username",
            "receiver",
            "receiver_username",
            "content",
            "is_direct",
            "created_at",
        ]
        read_only_fields = ["id", "sender", "sender_username", "receiver_username", "channel_name", "created_at"]
