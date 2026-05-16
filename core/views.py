from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import JWTAuthentication
from .models import NotificationEvent, Favorite
from .serializers import NotificationEventSerializer, FavoriteSerializer


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


class FavoriteListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = request.user.favorites.order_by('-created_at')
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data)

    def post(self, request):
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'status': 'error', 'message': 'project_id required'}, status=400)
        fav, created = Favorite.objects.get_or_create(user=request.user, project_id=project_id)
        serializer = FavoriteSerializer(fav)
        return Response(serializer.data, status=201 if created else 200)


class FavoriteDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            fav = Favorite.objects.get(pk=pk, user=request.user)
            fav.delete()
            return Response({'status': 'success'})
        except Favorite.DoesNotExist:
            return Response({'status': 'error', 'message': 'Not found'}, status=404)
