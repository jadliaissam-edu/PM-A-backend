from rest_framework import serializers

from .models import Role


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
