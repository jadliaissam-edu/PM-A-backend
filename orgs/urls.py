from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AcceptInvitationView, InvitationViewSet, OrganizationTreeView, OrganizationViewSet, WorkspaceViewSet


router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"workspaces", WorkspaceViewSet, basename="workspace")
router.register(r"invitations", InvitationViewSet, basename="invitation")


urlpatterns = [
    path("tree/", OrganizationTreeView.as_view(), name="organization-tree"),
    path("invitations/<uuid:invitation_id>/accept/", AcceptInvitationView.as_view(), name="accept-invitation"),
    path("", include(router.urls)),
]
