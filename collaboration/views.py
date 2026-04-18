from xml.etree.ElementTree import Comment

from django.shortcuts import render

from collaboration.models import Reaction
from collaboration.serializer import CommentSerializer, ReactionSerializer
from  rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView

class CommentCreateView(CreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class =  CommentSerializer

    def perform_create(self, serializer):
        ticket_id = self.kwargs['ticketId']
        serializer.save(
            ticket_id=ticket_id,
            author=self.request.user
        )

class CommentListView( ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def get_queryset(self):
        ticket_id = self.kwargs['ticketId']
        return Comment.objects.filter(ticket_id=ticket_id).order_by('created_at')

class CommentupdateView( CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class =  CommentSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)
     
class CommentDeleteView ( DestroyAPIView ): 
    authentication_classes = [JWTAuthentication] 
    permission_classes = [IsAuthenticated] 
    lookup_field = 'id'


    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)
    

class ReactionCreateView(CreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReactionSerializer

    def perform_create(self, serializer):
        comment_id = self.kwargs['commentId']

        serializer.save(
            comment_id=comment_id,
            user=self.request.user
        )

from rest_framework.generics import ListAPIView


class ReactionListView(ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ReactionSerializer

    def get_queryset(self):
        comment_id = self.kwargs['commentId']
        return Reaction.objects.filter(comment_id=comment_id)
    
class ReactionDeleteView(DestroyAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Reaction.objects.filter(user=self.request.user)
