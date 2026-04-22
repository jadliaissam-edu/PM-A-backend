from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.authentication import JWTAuthentication

from tickets.models import Ticket

from .models import Comment, Reaction
from .serializer import CommentSerializer, ReactionSerializer


class AuthenticatedAPIView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class CommentListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        comments = Comment.objects.filter(ticket_id=ticket_id, ticket__project_id=project_id).select_related("author").order_by("created_at")
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, project_id, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id, project_id=project_id)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(ticket=ticket, author=request.user)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(AuthenticatedAPIView):
    def get_object(self, project_id, ticket_id, comment_id):
        return get_object_or_404(Comment, id=comment_id, ticket_id=ticket_id, ticket__project_id=project_id)

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
        reactions = Reaction.objects.filter(comment_id=comment_id, comment__ticket_id=ticket_id, comment__ticket__project_id=project_id).select_related("user")
        return Response(ReactionSerializer(reactions, many=True).data)

    def post(self, request, project_id, ticket_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, ticket_id=ticket_id, ticket__project_id=project_id)
        serializer = ReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction = serializer.save(comment=comment, user=request.user)
        return Response(ReactionSerializer(reaction).data, status=status.HTTP_201_CREATED)


class ReactionDeleteView(AuthenticatedAPIView):
    def delete(self, request, project_id, ticket_id, comment_id, reaction_id):
        reaction = get_object_or_404(
            Reaction,
            id=reaction_id,
            comment_id=comment_id,
            comment__ticket_id=ticket_id,
            comment__ticket__project_id=project_id,
        )
        reaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
