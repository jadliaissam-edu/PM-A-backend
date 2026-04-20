from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, WorkspaceViewSet, InvitationViewSet

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet)
router.register(r'workspaces', WorkspaceViewSet)
router.register(r'invitations', InvitationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
