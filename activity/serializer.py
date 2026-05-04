from rest_framework import serializers
from .models import ActivityLog

class ActivityLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    target_name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id", "actor", "actor_username", "action", "description", 
            "project_id", "target_name", "old_value", "new_value", "created_at"
        ]

    def get_target_name(self, obj):
        try:
            return str(obj.content_object)
        except:
            return f"{obj.content_type} {obj.object_id}"
