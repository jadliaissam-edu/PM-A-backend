from rest_framework import serializers
from .models_ticket_history import TicketHistory

class TicketHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketHistory
        fields = "__all__"
