from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Ticket
from .models_ticket_history import TicketHistory
from .serializers_ticket_history import TicketHistorySerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_history(request, project_id, ticket_id):
    history = TicketHistory.objects.filter(ticket__id=ticket_id, ticket__project__id=project_id).order_by("-timestamp")
    serializer = TicketHistorySerializer(history, many=True)
    return Response(serializer.data)
