from django.urls import path
from .views import ProjectActivityView, TicketHistoryView, UserActivityView, AuditLogView

urlpatterns = [
    path("audit/", AuditLogView.as_view(), name="global-audit"),
    path("projects/<uuid:project_id>/activity/", ProjectActivityView.as_view(), name="project-activity"),
    path("tickets/<uuid:ticket_id>/history/", TicketHistoryView.as_view(), name="ticket-history"),
    path("users/me/activity/", UserActivityView.as_view(), name="user-me-activity"),
]
