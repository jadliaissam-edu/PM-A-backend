from django.contrib.auth import get_user_model
from rest_framework import serializers

from orgs.models import Workspace

from .models import BoardColumn, Project, ProjectBoard, ProjectMember, Sprint, SprintReport, Release


User = get_user_model()


class CurrentUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMember
        fields = ["id", "user", "username", "email", "full_name", "role"]
        read_only_fields = ["id", "username", "email", "full_name"]

    def get_full_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.username


class WorkspaceSummarySerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "name", "visibility", "organization_id", "organization_name"]


class ProjectSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSummarySerializer(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        source="workspace",
        queryset=Workspace.objects.select_related("organization").all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    organization_id = serializers.UUIDField(source="workspace.organization.id", read_only=True)
    organization_name = serializers.CharField(source="workspace.organization.name", read_only=True)
    board_id = serializers.UUIDField(source="board.id", read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    ticket_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "type",
            "visibility",
            "status",
            "created_at",
            "workspace",
            "workspace_id",
            "organization_id",
            "organization_name",
            "board_id",
            "member_count",
            "ticket_count",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "workspace",
            "organization_id",
            "organization_name",
            "board_id",
            "member_count",
            "ticket_count",
        ]


class BoardColumnSerializer(serializers.ModelSerializer):
    ticket_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = BoardColumn
        fields = ["id", "name", "position", "wip_limit", "is_done_column", "ticket_count"]
        read_only_fields = ["id", "ticket_count"]


class ProjectBoardSerializer(serializers.ModelSerializer):
    columns = BoardColumnSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectBoard
        fields = ["id", "project", "board_type", "view_mode", "columns"]
        read_only_fields = ["id", "project", "columns"]


class BoardConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBoard
        fields = ["board_type", "view_mode"]


class SprintReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SprintReport
        fields = [
            "total_tickets",
            "done_tickets",
            "remaining_tickets",
            "completion_rate",
        ]


class SprintSerializer(serializers.ModelSerializer):
    report = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = [
            "id",
            "name",
            "goal",
            "start_date",
            "end_date",
            "status",
            "report",
        ]
        read_only_fields = ["id", "report"]

    def get_report(self, obj):
        latest_report = obj.reports.order_by("-id").first()
        if not latest_report:
            return None
        return SprintReportSerializer(latest_report).data


class ReleaseSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Release
        fields = [
            "id",
            "project",
            "project_name",
            "tag",
            "target_date",
            "description",
            "status",
        ]
        read_only_fields = ["id", "project_name"]
