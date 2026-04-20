from rest_framework import serializers
from .models import Organization, Workspace, Invitation

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'created_at']

class WorkspaceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Workspace
        fields = ['id', 'organization', 'organization_name', 'name', 'visibility']

class InvitationSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = Invitation
        fields = ['id', 'workspace', 'workspace_name', 'email', 'invite_link', 'expires_at']
