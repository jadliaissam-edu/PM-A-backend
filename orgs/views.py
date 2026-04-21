from django.db.models import Count, Prefetch
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from project.models import Project

from .models import Invitation, Organization, Workspace
from .serializers import (
    InvitationSerializer,
    OrganizationSerializer,
    OrganizationTreeSerializer,
    WorkspaceSerializer,
)


class AuthenticatedModelViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class OrganizationViewSet(AuthenticatedModelViewSet):
    queryset = Organization.objects.annotate(
        workspace_count=Count("workspaces", distinct=True),
        project_count=Count("workspaces__projects", distinct=True),
    ).order_by("name")
    serializer_class = OrganizationSerializer


class WorkspaceViewSet(AuthenticatedModelViewSet):
    queryset = Workspace.objects.select_related("organization").annotate(
        project_count=Count("projects", distinct=True)
    ).order_by("name")
    serializer_class = WorkspaceSerializer


class InvitationViewSet(AuthenticatedModelViewSet):
    queryset = Invitation.objects.select_related("workspace").order_by("-expires_at")
    serializer_class = InvitationSerializer


class OrganizationTreeView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organizations = Organization.objects.prefetch_related(
            Prefetch(
                "workspaces",
                queryset=Workspace.objects.prefetch_related(
                    Prefetch("projects", queryset=Project.objects.order_by("-created_at"))
                ).order_by("name"),
            )
        ).order_by("name")
        return Response(OrganizationTreeSerializer(organizations, many=True).data)
