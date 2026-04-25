from django.urls import path

from .views import (
    BacklogAddToSprintView,
    BacklogDeleteView,
    BacklogListCreateView,
    BacklogPrioritizeView,
    ProjectTicketListCreateView,
    ReleaseCloseView,
    ReleaseDashboardView,
    ReleaseDetailView,
    ReleaseIssuesSummaryView,
    ReleaseListCreateView,
    TicketAssigneeDeleteView,
    TicketAssigneeListCreateView,
    TicketAttachmentDeleteView,
    TicketAttachmentListCreateView,
    TicketDetailView,
    TicketLabelsView,
    TicketLinkDeleteView,
    TicketLinkListCreateView,
    TicketMovementListView,
    TicketMoveView,
    TicketStatusView,
    TicketTimeEntryListCreateView,
    GlobalTicketListView
)
from .views_search import TicketSearchView


urlpatterns = [
    path("tickets/", GlobalTicketListView.as_view(), name="global-ticket-list"),
    path("projects/<uuid:project_id>/tickets/", ProjectTicketListCreateView.as_view()),
    path("projects/<uuid:project_id>/tickets/<uuid:ticket_id>/", TicketDetailView.as_view()),
    path("projects/<uuid:project_id>/tickets/<uuid:ticket_id>/status/", TicketStatusView.as_view()),
    path("projects/<uuid:project_id>/tickets/<uuid:ticket_id>/labels/", TicketLabelsView.as_view()),
    path("projects/<uuid:project_id>/tickets/<uuid:ticket_id>/assignees/", TicketAssigneeListCreateView.as_view()),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/assignees/<int:user_id>/",
        TicketAssigneeDeleteView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/time-entries/",
        TicketTimeEntryListCreateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/attachments/",
        TicketAttachmentListCreateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/attachments/<uuid:attachment_id>/",
        TicketAttachmentDeleteView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/links/",
        TicketLinkListCreateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/links/<uuid:link_id>/",
        TicketLinkDeleteView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/board/tickets/<uuid:ticket_id>/move/",
        TicketMoveView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/board/tickets/<uuid:ticket_id>/movements/",
        TicketMovementListView.as_view(),
    ),
    path("projects/<uuid:project_id>/backlog/", BacklogListCreateView.as_view()),
    path(
        "projects/<uuid:project_id>/backlog/<uuid:backlog_item_id>/prioritize/",
        BacklogPrioritizeView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/backlog/<uuid:backlog_item_id>/add-to-sprint/",
        BacklogAddToSprintView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/backlog/<uuid:backlog_item_id>/",
        BacklogDeleteView.as_view(),
    ),
    path("projects/<uuid:project_id>/releases/", ReleaseListCreateView.as_view()),
    path("projects/<uuid:project_id>/releases/<uuid:release_id>/", ReleaseDetailView.as_view()),
    path(
        "projects/<uuid:project_id>/releases/<uuid:release_id>/close/",
        ReleaseCloseView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/releases/<uuid:release_id>/dashboard/",
        ReleaseDashboardView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/releases/<uuid:release_id>/issues-summary/",
        ReleaseIssuesSummaryView.as_view(),
    ),
    path("projects/<uuid:project_id>/tickets/search", TicketSearchView.as_view()),
]
