from rest_framework import serializers

from project.models import Project

from .models import Invitation, Organization, Workspace


class ProjectTreeSerializer(serializers.ModelSerializer):
    board_id = serializers.UUIDField(source="board.id", read_only=True)

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
            "board_id",
        ]


class OrganizationSerializer(serializers.ModelSerializer):
    workspace_count = serializers.IntegerField(read_only=True)
    project_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "created_at", "workspace_count", "project_count"]


class WorkspaceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    project_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workspace
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "visibility",
            "project_count",
        ]


class WorkspaceTreeSerializer(serializers.ModelSerializer):
    projects = ProjectTreeSerializer(many=True, read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "name", "visibility", "projects"]


class OrganizationTreeSerializer(serializers.ModelSerializer):
    workspaces = WorkspaceTreeSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "created_at", "workspaces"]


class InvitationSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)

    class Meta:
        model = Invitation
        fields = ["id", "workspace", "workspace_name", "email", "invite_link", "expires_at"]
