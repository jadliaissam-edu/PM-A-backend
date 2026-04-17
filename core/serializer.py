from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import BoardColumn, Project, ProjectBoard, Role


User = get_user_model()


class CurrentUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProjectSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'owner',
            'owner_username',
            'is_archived',
            'is_closed',
            'created_at',
        ]
        read_only_fields = ['id', 'owner', 'owner_username', 'created_at']


class BoardColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardColumn
        fields = ['id', 'board', 'name', 'position']
        read_only_fields = ['id', 'board']


class ProjectBoardSerializer(serializers.ModelSerializer):
    columns = BoardColumnSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectBoard
        fields = ['id', 'project', 'columns', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Role
        fields = [
            'id',
            'project',
            'user',
            'user_username',
            'role_name',
            'permissions',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'project']