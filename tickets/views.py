from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated 
from rest_framework_simplejwt.authentication import JWTAuthentication 
from rest_framework.authentication import SessionAuthentication 
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Ticket 
class createTicketView(APIView):
    Authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None): 
        data = request.data 
        Ticket.objects.create(
            title=data.get('title'),
            description=data.get('description'),
            project_id=data.get('project_id'),
            created_by=request.user
        )
        # Logic to create a ticket goes here 
        return Response({"message": "Ticket created successfully"}, status=201) 
    
    def 