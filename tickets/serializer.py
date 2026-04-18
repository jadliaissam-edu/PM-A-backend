from rest_framework import serializers


from .models import Attachment, Role, TimeEntry


from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'title', 'description_markdown', 'type', 'priority', 'status']


class TimeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = '__all__'
        read_only_fields = ['id', 'user', 'ticket']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_by', 'file_name', 'file_size', 'uploaded_at']

    