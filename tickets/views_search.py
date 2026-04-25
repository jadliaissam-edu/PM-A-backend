from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q
from .models import Ticket
from .serializer import TicketSerializer

class TicketSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        q = request.query_params.get("q", "")
        status = request.query_params.get("status")
        assignee = request.query_params.get("assignee")
        priority = request.query_params.get("priority")

        tickets = Ticket.objects.filter(project_id=project_id)

        if q:
            tickets = tickets.annotate(
                search=SearchVector("title", "description_markdown")
            ).filter(search=SearchQuery(q))
        if status:
            tickets = tickets.filter(status=status)
        if priority:
            tickets = tickets.filter(priority=priority)
        if assignee:
            tickets = tickets.filter(assignments__user_id=assignee)

        tickets = tickets.distinct().order_by("-created_at")
        return Response(TicketSerializer(tickets, many=True).data)
