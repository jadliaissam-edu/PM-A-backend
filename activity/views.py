from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from accounts.authentication import JWTAuthentication

from .models import ActivityLog
from .serializer import ActivityLogSerializer

class AuthenticatedAPIView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

class ProjectActivityView(AuthenticatedAPIView):
    def get(self, request, project_id):
        activities = ActivityLog.objects.filter(project_id=project_id).order_by("-created_at")
        return Response(ActivityLogSerializer(activities, many=True).data)

class TicketHistoryView(AuthenticatedAPIView):
    def get(self, request, ticket_id):
        ticket_ct = ContentType.objects.get(app_label='tickets', model='ticket')
        activities = ActivityLog.objects.filter(content_type=ticket_ct, object_id=ticket_id).order_by("-created_at")
        return Response(ActivityLogSerializer(activities, many=True).data)

class UserActivityView(AuthenticatedAPIView):
    def get(self, request):
        activities = ActivityLog.objects.filter(actor=request.user).order_by("-created_at")
        return Response(ActivityLogSerializer(activities, many=True).data)
