from django.urls import path

from .views import CurrentUserProfileView, health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('users/me/', CurrentUserProfileView.as_view(), name='current-user-profile'),
]