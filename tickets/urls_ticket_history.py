from django.urls import path
from .views_ticket_history import ticket_history

urlpatterns = [
    path('projects/<uuid:project_id>/tickets/<uuid:ticket_id>/history/', ticket_history),
]
