from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import JWTAuthentication
from .models import Space, NotificationEvent
from .serializers import SpaceSerializer, NotificationEventSerializer

@api_view(["GET"])
def space_list(request):
    spaces = Space.objects.all()
    serializer = SpaceSerializer(spaces, many=True)
    return Response(serializer.data)

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