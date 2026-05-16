from rest_framework import serializers
from .models import NotificationEvent

class NotificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = ['id', 'project_id', 'event_type', 'payload_json', 'is_read', 'created_at']


from .models import Favorite

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'project_id', 'created_at']