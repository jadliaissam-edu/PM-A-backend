from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AcceptInvitationView, InvitationViewSet, OrganizationTreeView, OrganizationViewSet, WorkspaceViewSet, OrganizationMemberView


router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"workspaces", WorkspaceViewSet, basename="workspace")
router.register(r"invitations", InvitationViewSet, basename="invitation")


urlpatterns = [
    path("tree/", OrganizationTreeView.as_view(), name="organization-tree"),
    path("organizations/<uuid:org_id>/members/", OrganizationMemberView.as_view(), name="organization-members"),
    path("invitations/accept/", AcceptInvitationView.as_view(), name="accept-invitation-param"),
    path("invitations/<uuid:invitation_id>/accept/", AcceptInvitationView.as_view(), name="accept-invitation"),
    path("", include(router.urls)),
]
