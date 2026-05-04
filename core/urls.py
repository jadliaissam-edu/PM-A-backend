from django.urls import path

from core.views import (
    NotificationListView, 
    MarkNotificationReadView, 
    MarkAllNotificationsReadView,
    NotificationUnreadCountView,
    NotificationMarkReadBulkView
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/unread-count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/mark-read-bulk/", NotificationMarkReadBulkView.as_view(), name="notification-mark-read-bulk"),
    path("notifications/<uuid:pk>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
    path("notifications/read-all/", MarkAllNotificationsReadView.as_view(), name="notification-read-all"),
]
