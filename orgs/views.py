from django.db import models
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.authentication import JWTAuthentication

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
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        # organizations where user is owner OR has membership
        return Organization.objects.filter(
            models.Q(owner=self.request.user) |
            models.Q(workspaces__members__user=self.request.user) |
            models.Q(workspaces__projects__members__user=self.request.user)
        ).annotate(
            workspace_count=Count("workspaces", distinct=True),
            project_count=Count("workspaces__projects", distinct=True),
        ).distinct().order_by("name")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class WorkspaceViewSet(AuthenticatedModelViewSet):
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        qs = Workspace.objects.filter(
            projects__members__user=self.request.user
        ).select_related("organization").annotate(
            project_count=Count("projects", distinct=True)
        ).distinct().order_by("name")
        org_id = self.request.query_params.get("organization")
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


class InvitationViewSet(AuthenticatedModelViewSet):
    queryset = Invitation.objects.select_related("workspace").order_by("-expires_at")
    serializer_class = InvitationSerializer

    def perform_create(self, serializer):
        invitation = serializer.save()
        
        # Send email
        context = {
            'workspace_name': invitation.workspace.name,
            'invite_link': invitation.invite_link,
        }
        
        html_message = render_to_string('orgs/emails/invitation.html', context)
        plain_message = f"Rejoignez {invitation.workspace.name} sur AgileFlow : {invitation.invite_link}"
        
        try:
            send_mail(
                subject=f"Invitation à rejoindre {invitation.workspace.name} sur AgileFlow",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send invitation email: {e}")

class AcceptInvitationView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, invitation_id):
        invitation = get_object_or_404(Invitation, id=invitation_id)
        if invitation.is_accepted:
             return Response({"detail": "Invitation already accepted."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Link user to workspace
        from .models import WorkspaceMember
        WorkspaceMember.objects.get_or_create(
            workspace=invitation.workspace,
            user=request.user,
            defaults={'role': invitation.role}
        )
        
        invitation.is_accepted = True
        invitation.save(update_fields=['is_accepted'])
        
        return Response({"detail": "Successfully joined workspace."}, status=status.HTTP_200_OK)


class OrganizationTreeView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organizations = Organization.objects.filter(
            workspaces__projects__members__user=request.user
        ).prefetch_related(
            Prefetch(
                "workspaces",
                queryset=Workspace.objects.filter(
                    projects__members__user=request.user
                ).prefetch_related(
                    Prefetch(
                        "projects", 
                        queryset=Project.objects.filter(
                            members__user=request.user
                        ).order_by("-created_at")
                    )
                ).order_by("name"),
            )
        ).distinct().order_by("name")
        return Response(OrganizationTreeSerializer(organizations, many=True).data)
