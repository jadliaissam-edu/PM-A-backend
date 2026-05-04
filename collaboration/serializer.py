from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import ChatChannel, ChatMessage, Comment, Reaction


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    entity_type = serializers.CharField(write_only=True, required=False)
    entity_id = serializers.UUIDField(write_only=True, required=False)
    
    # We can also expose the content_type name for convenience in GET
    object_type = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "object_type",
            "object_id",
            "author",
            "author_username",
            "body",
            "mentions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "author_username", "created_at", "updated_at", "object_type", "object_id"]

    def get_object_type(self, obj):
        reverse_mapping = {
            'ticket': 'ticket',
            'projectdocument': 'document',
            'projectfile': 'file',
            'chatmessage': 'message'
        }
        return reverse_mapping.get(obj.content_type.model, obj.content_type.model)

    def create(self, validated_data):
        entity_type = validated_data.pop("entity_type", None)
        entity_id = validated_data.pop("entity_id", None)
        
        if not entity_type or not entity_id:
            raise serializers.ValidationError("entity_type and entity_id are required for creation")

        type_mapping = {
            'ticket': 'tickets.ticket',
            'document': 'project.projectdocument',
            'file': 'project.projectfile',
            'message': 'collaboration.chatmessage'
        }
        
        if entity_type not in type_mapping:
            raise serializers.ValidationError({"entity_type": f"Invalid entity type. Choices: {list(type_mapping.keys())}"})
            
        app_label, model_name = type_mapping[entity_type].split('.')
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({"entity_type": "Content type not found"})
        
        return Comment.objects.create(
            content_type=content_type,
            object_id=entity_id,
            **validated_data
        )


class ReactionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "comment", "user", "username", "type", "created_at"]
        read_only_fields = ["id", "comment", "user", "username", "created_at"]


class ChatChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatChannel
        fields = ["id", "workspace", "project", "is_direct", "participants", "name", "description", "created_at"]


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
