from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Space, NotificationEvent
from .serializers import SpaceSerializer, NotificationEventSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(["GET"])
def space_list(request):
    spaces = Space.objects.all()
    serializer = SpaceSerializer(spaces, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    notifications = NotificationEvent.objects.filter(user=request.user).order_by("-created_at")[:50]
    serializer = NotificationEventSerializer(notifications, many=True)
    return Response(serializer.data)