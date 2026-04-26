from rest_framework import serializers
from .models import NotificationEvent, Space

class NotificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = ['id', 'project_id', 'event_type', 'payload_json', 'is_read', 'created_at']

class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = '__all__'