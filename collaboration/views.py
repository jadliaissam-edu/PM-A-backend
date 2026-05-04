from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.authentication import JWTAuthentication

from tickets.models import Ticket

from .models import ChatChannel, ChatMessage, Comment, Reaction
from .serializer import ChatChannelSerializer, ChatMessageSerializer, CommentSerializer, ReactionSerializer
from activity.utils import log_activity


class AuthenticatedAPIView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class WorkspaceChannelListCreateView(AuthenticatedAPIView):
    def get(self, request, workspace_id):
        from orgs.models import WorkspaceMember
        is_member = WorkspaceMember.objects.filter(user=request.user, workspace_id=workspace_id).exists()
        if not is_member:
            return Response({"error": "Not a member of this workspace"}, status=status.HTTP_403_FORBIDDEN)
        
        channels = ChatChannel.objects.filter(workspace_id=workspace_id, is_direct=False)
        return Response(ChatChannelSerializer(channels, many=True).data)

    def post(self, request, workspace_id):
        from orgs.models import WorkspaceMember
        is_member = WorkspaceMember.objects.filter(user=request.user, workspace_id=workspace_id).exists()
        if not is_member:
            return Response({"error": "Not a member of this workspace"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChatChannelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        channel = serializer.save(workspace_id=workspace_id, is_direct=False)
        return Response(ChatChannelSerializer(channel).data, status=status.HTTP_201_CREATED)


class ProjectChannelListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id):
        from project.models import ProjectMember
        is_member = ProjectMember.objects.filter(user=request.user, project_id=project_id).exists()
        if not is_member:
            return Response({"error": "Not a member of this project"}, status=status.HTTP_403_FORBIDDEN)
        
        channels = ChatChannel.objects.filter(project_id=project_id, is_direct=False)
        return Response(ChatChannelSerializer(channels, many=True).data)

    def post(self, request, project_id):
        from project.models import ProjectMember
        is_member = ProjectMember.objects.filter(user=request.user, project_id=project_id).exists()
        if not is_member:
            return Response({"error": "Not a member of this project"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChatChannelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        channel = serializer.save(project_id=project_id, is_direct=False)
        return Response(ChatChannelSerializer(channel).data, status=status.HTTP_201_CREATED)


class ChatMessageListCreateView(AuthenticatedAPIView):
    def get(self, request, channel_id):
        channel = get_object_or_404(ChatChannel, id=channel_id)
        # Permission check: must be participant or member of workspace/project
        can_access = False
        if channel.is_direct:
            can_access = channel.participants.filter(id=request.user.id).exists()
        elif channel.project:
            from project.models import ProjectMember
            can_access = ProjectMember.objects.filter(user=request.user, project=channel.project).exists()
        elif channel.workspace:
            from orgs.models import WorkspaceMember
            can_access = WorkspaceMember.objects.filter(user=request.user, workspace=channel.workspace).exists()
            
        if not can_access:
            return Response({"error": "No access to this channel"}, status=status.HTTP_403_FORBIDDEN)
            
        messages = ChatMessage.objects.filter(channel=channel).select_related("sender").order_by("created_at")
        return Response(ChatMessageSerializer(messages, many=True).data)

    def post(self, request, channel_id):
        channel = get_object_or_404(ChatChannel, id=channel_id)
        # Permission check same as GET
        can_access = False
        if channel.is_direct:
            can_access = channel.participants.filter(id=request.user.id).exists()
        elif channel.project:
            from project.models import ProjectMember
            can_access = ProjectMember.objects.filter(user=request.user, project=channel.project).exists()
        elif channel.workspace:
            from orgs.models import WorkspaceMember
            can_access = WorkspaceMember.objects.filter(user=request.user, workspace=channel.workspace).exists()

        if not can_access:
            return Response({"error": "No access to this channel"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(channel=channel, sender=request.user)
        return Response(ChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class DirectChannelGetCreateView(AuthenticatedAPIView):
    """Gets or creates a DM channel between current user and recipient."""
    def post(self, request):
        recipient_id = request.data.get("recipient_id")
        if not recipient_id:
            return Response({"error": "recipient_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        recipient = get_object_or_404(User, id=recipient_id)
        
        
        channel = ChatChannel.objects.filter(is_direct=True, participants=request.user).filter(participants=recipient).first()
        
        if not channel:
            channel = ChatChannel.objects.create(is_direct=True, name=f"DM: {request.user.username} - {recipient.username}")
            channel.participants.add(request.user, recipient)
            
        return Response(ChatChannelSerializer(channel).data)


class GlobalCommentViewSet(viewsets.ModelViewSet):
    """Global endpoint for comments on tickets, documents, files, and messages."""
    queryset = Comment.objects.all().select_related("author", "content_type")
    serializer_class = CommentSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        
        # Try to find a project_id
        project_id = None
        target = comment.content_object
        if hasattr(target, 'project_id'):
            project_id = target.project_id
        elif hasattr(target, 'project'):
            project_id = target.project.id
            
        log_activity(
            actor=self.request.user,
            target=target,
            action="comment",
            description=f"Commented on {comment.content_type.model} '{target}'",
            project_id=project_id,
        )
        
        # Dispatch Mention Notifications
        if getattr(comment, 'mentions', None):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for username in comment.mentions:
                try:
                    user = User.objects.get(username=username)
                    if user.email:
                        send_mention_notification_email(
                            recipient_email=user.email,
                            author_name=self.request.user.username,
                            content_snippet=comment.body[:50] + "...",
                            target_name=str(target),
                            target_url=f"/projects/{project_id}/tickets/{target.id}" if hasattr(target, 'id') else "#"
                        )
                except User.DoesNotExist:
                    continue

    def get_queryset(self):
        queryset = super().get_queryset()
        entity_type = self.request.query_params.get('entity_type')
        entity_id = self.request.query_params.get('entity_id')
        
        if entity_type and entity_id:
            type_mapping = {
                'ticket': 'tickets.ticket',
                'document': 'project.projectdocument',
                'file': 'project.projectfile',
                'message': 'collaboration.chatmessage'
            }
            if entity_type in type_mapping:
                app_label, model_name = type_mapping[entity_type].split('.')
                try:
                    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                    queryset = queryset.filter(content_type=content_type, object_id=entity_id)
                except ContentType.DoesNotExist:
                    pass
        
        return queryset


class CommentListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        ticket_ct = ContentType.objects.get(app_label='tickets', model='ticket')
        comments = Comment.objects.filter(content_type=ticket_ct, object_id=ticket_id).select_related("author").order_by("created_at")
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, project_id, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id, project_id=project_id)
        
        data = request.data.copy()
        if 'entity_type' not in data: data['entity_type'] = 'ticket'
        if 'entity_id' not in data: data['entity_id'] = str(ticket_id)
        
        serializer = CommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(author=request.user)
        
        log_activity(
            actor=request.user,
            target=ticket,
            action="comment",
            description=f"Commented on ticket '{ticket.title}'",
            project_id=project_id,
        )
        
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(AuthenticatedAPIView):
    def get_object(self, project_id, ticket_id, comment_id):
        ticket_ct = ContentType.objects.get(app_label='tickets', model='ticket')
        return get_object_or_404(Comment, id=comment_id, content_type=ticket_ct, object_id=ticket_id)

    def patch(self, request, project_id, ticket_id, comment_id):
        comment = self.get_object(project_id, ticket_id, comment_id)
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CommentSerializer(comment).data)

    def delete(self, request, project_id, ticket_id, comment_id):
        comment = self.get_object(project_id, ticket_id, comment_id)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReactionListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id, comment_id):
        ticket_ct = ContentType.objects.get(app_label='tickets', model='ticket')
        reactions = Reaction.objects.filter(comment_id=comment_id, comment__content_type=ticket_ct, comment__object_id=ticket_id).select_related("user")
        return Response(ReactionSerializer(reactions, many=True).data)

    def post(self, request, project_id, ticket_id, comment_id):
        ticket_ct = ContentType.objects.get(app_label='tickets', model='ticket')
        comment = get_object_or_404(Comment, id=comment_id, content_type=ticket_ct, object_id=ticket_id)
        serializer = ReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction = serializer.save(comment=comment, user=request.user)
        return Response(ReactionSerializer(reaction).data, status=status.HTTP_201_CREATED)


class ReactionDeleteView(AuthenticatedAPIView):
    def delete(self, request, project_id, ticket_id, comment_id, reaction_id):
        ticket_ct = ContentType.objects.get(app_label='tickets', model='ticket')
        reaction = get_object_or_404(
            Reaction,
            id=reaction_id,
            comment_id=comment_id,
            comment__content_type=ticket_ct,
            comment__object_id=ticket_id,
        )
        reaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
