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
from .models import WorkspaceMember
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
        # include workspaces where the user is a project member, a workspace member,
        # or the owner of the organization so creators see newly created workspaces
        qs = Workspace.objects.filter(
            models.Q(projects__members__user=self.request.user) |
            models.Q(members__user=self.request.user) |
            models.Q(organization__owner=self.request.user)
        ).select_related("organization").annotate(
            project_count=Count("projects", distinct=True)
        ).distinct().order_by("name")
        org_id = self.request.query_params.get("organization")
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs

    def perform_create(self, serializer):
        # create the workspace
        workspace = serializer.save()
        # ensure the creator is a workspace member so they see it in listings
        try:
            WorkspaceMember.objects.get_or_create(workspace=workspace, user=self.request.user, defaults={"role": "Owner"})
        except Exception:
            pass


from activity.emails import send_workspace_invitation_email


class InvitationViewSet(AuthenticatedModelViewSet):
    queryset = Invitation.objects.select_related("workspace").order_by("-expires_at")
    serializer_class = InvitationSerializer

    def perform_create(self, serializer):
        invitation = serializer.save()
        
        # Check if user already exists and is a member
        from django.contrib.auth.models import User
        user = User.objects.filter(email=invitation.email).first()
        if user and WorkspaceMember.objects.filter(workspace=invitation.workspace, user=user).exists():
            invitation.is_accepted = True
            invitation.save(update_fields=['is_accepted'])
            return
            
        # Send email in the background (simulated by helper)
        send_workspace_invitation_email(
            recipient_email=invitation.email,
            workspace_name=invitation.workspace.name,
            invite_link=invitation.invite_link
        )

class AcceptInvitationView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, invitation_id=None):
        if invitation_id:
            invitation = get_object_or_404(Invitation, id=invitation_id)
        else:
            workspace_id = request.data.get('workspace')
            if not workspace_id:
                return Response({"detail": "Workspace ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            invitation = Invitation.objects.filter(
                workspace_id=workspace_id, 
                email__iexact=request.user.email, 
                is_accepted=False
            ).first()
            
            if not invitation:
                # If no invitation found for CURRENT user email, check if there's one for the email in request data
                # to provide a better error message.
                req_email = request.data.get('email')
                if req_email and req_email.lower() != request.user.email.lower():
                     return Response({"detail": f"This invitation was sent to {req_email}, but you are logged in as {request.user.email}."}, status=status.HTTP_403_FORBIDDEN)
                
                return Response({"detail": "No pending invitation found for this workspace."}, status=status.HTTP_404_NOT_FOUND)

        if invitation.is_accepted:
             return Response({"detail": "Invitation already accepted."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Link user to workspace
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
        

class OrganizationMemberView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        # Unique users from workspaces and the owner
        from django.contrib.auth.models import User
        workspace_users = User.objects.filter(workspace_memberships__workspace__organization=org)
        owner = User.objects.filter(id=org.owner_id) if org.owner_id else User.objects.none()
        
        users = (workspace_users | owner).distinct().order_by('username')
        
        payload = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar_url": getattr(user, 'avatar_url', None), # Assume it might exist or handle gracefully
            }
            for user in users
        ]
        return Response(payload)
