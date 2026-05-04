from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommentDetailView,
    CommentListCreateView,
    ReactionDeleteView,
    ReactionListCreateView,
    WorkspaceChannelListCreateView,
    ProjectChannelListCreateView,
    ChatMessageListCreateView,
    DirectChannelGetCreateView,
    GlobalCommentViewSet,
)

router = DefaultRouter()
router.register(r"comments", GlobalCommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "workspaces/<uuid:workspace_id>/channels/",
        WorkspaceChannelListCreateView.as_view(),
        name="workspace-channels",
    ),
    path(
        "projects/<uuid:project_id>/channels/",
        ProjectChannelListCreateView.as_view(),
        name="project-channels",
    ),
    path(
        "channels/<uuid:channel_id>/messages/",
        ChatMessageListCreateView.as_view(),
        name="channel-messages",
    ),
    path(
        "channels/direct/",
        DirectChannelGetCreateView.as_view(),
        name="direct-channel",
    ),
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
