from django.urls import path

from core.views import space_list, user_notifications

urlpatterns = [
    path("spaces/", space_list),
    path("notifications/", user_notifications),
]
