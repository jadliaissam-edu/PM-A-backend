from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import JWTAuthentication
from .models import NotificationEvent
from .serializers import NotificationEventSerializer


class NotificationListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = NotificationEvent.objects.filter(user=request.user).order_by('-created_at')
        serializer = NotificationEventSerializer(notifications, many=True)
        return Response(serializer.data)

class MarkNotificationReadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = NotificationEvent.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({"status": "success"})
        except NotificationEvent.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=404)

class MarkAllNotificationsReadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        NotificationEvent.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "success"})
class NotificationUnreadCountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationEvent.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})


class NotificationMarkReadBulkView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notification_ids = request.data.get("notification_ids", [])
        if not isinstance(notification_ids, list):
            return Response({"status": "error", "message": "notification_ids must be a list"}, status=400)
            
        NotificationEvent.objects.filter(user=request.user, id__in=notification_ids).update(is_read=True)
        return Response({"status": "success", "marked_count": len(notification_ids)})
