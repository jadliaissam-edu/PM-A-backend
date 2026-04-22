from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attachment, BacklogItem, Ticket, TicketAssignment, TicketLink, TimeEntry


User = get_user_model()


class TicketAssignmentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = TicketAssignment
        fields = ["id", "user", "username", "email", "assigned_at"]
        read_only_fields = ["id", "username", "email", "assigned_at"]


class TicketSerializer(serializers.ModelSerializer):
    assignments = TicketAssignmentSerializer(many=True, read_only=True)
    current_column_name = serializers.CharField(source="current_column.name", read_only=True)
    sprint_name = serializers.CharField(source="sprint.name", read_only=True)
    release_tag = serializers.CharField(source="release.tag", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "project",
            "current_column",
            "current_column_name",
            "sprint",
            "sprint_name",
            "release",
            "release_tag",
            "title",
            "description_markdown",
            "type",
            "priority",
            "status",
            "labels",
            "estimate_story_points",
            "estimate_hours",
            "created_at",
            "assignments",
        ]
        read_only_fields = ["id", "created_at", "assignments"]
        extra_kwargs = {
            "project": {"read_only": True},
        }


class TimeEntrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            "id",
            "ticket",
            "user",
            "username",
            "hours_spent",
            "comment",
            "started_at",
            "ended_at",
        ]
        read_only_fields = ["id", "user", "username", "ticket"]


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = Attachment
        fields = [
            "id",
            "ticket",
            "uploaded_by",
            "uploaded_by_username",
            "file_name",
            "file_url",
            "mime_type",
            "file_size",
            "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_by", "uploaded_by_username", "uploaded_at"]


class TicketLinkSerializer(serializers.ModelSerializer):
    target_ticket_title = serializers.CharField(source="target_ticket.title", read_only=True)

    class Meta:
        model = TicketLink
        fields = [
            "id",
            "source_ticket",
            "target_ticket",
            "target_ticket_title",
            "link_type",
            "created_at",
        ]
        read_only_fields = ["id", "source_ticket", "created_at", "target_ticket_title"]


class BacklogItemSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    ticket_id = serializers.PrimaryKeyRelatedField(
        source="ticket", queryset=Ticket.objects.all(), write_only=True
    )

    class Meta:
        model = BacklogItem
        fields = [
            "id",
            "project",
            "ticket",
            "ticket_id",
            "rank",
            "priority_score",
            "created_at",
        ]
        read_only_fields = ["id", "project", "ticket", "created_at"]
