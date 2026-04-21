from django.urls import path

from .views import CommentDetailView, CommentListCreateView, ReactionDeleteView, ReactionListCreateView


urlpatterns = [
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/comments/",
        CommentListCreateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/comments/<uuid:comment_id>/",
        CommentDetailView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/comments/<uuid:comment_id>/reactions/",
        ReactionListCreateView.as_view(),
    ),
    path(
        "projects/<uuid:project_id>/tickets/<uuid:ticket_id>/comments/<uuid:comment_id>/reactions/<uuid:reaction_id>/",
        ReactionDeleteView.as_view(),
    ),
]
