from django.urls import path

from core.views import space_list, NotificationListView, MarkNotificationReadView, MarkAllNotificationsReadView
urlpatterns = [
    path("spaces/", space_list),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<uuid:pk>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
    path("notifications/read-all/", MarkAllNotificationsReadView.as_view(), name="notification-read-all"),
]
