from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (
    ChatChannelViewSet,
    ChatMessageViewSet,
    CommentDetailView,
    CommentListCreateView,
    ReactionDeleteView,
    ReactionListCreateView,
)

router = SimpleRouter()
router.register(r"channels", ChatChannelViewSet, basename="chat-channels")
router.register(r"messages", ChatMessageViewSet, basename="chat-messages")

urlpatterns = [
    path("", include(router.urls)),
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
