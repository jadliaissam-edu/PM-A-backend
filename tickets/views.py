from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated 
from rest_framework_simplejwt.authentication import JWTAuthentication 
from rest_framework.authentication import SessionAuthentication 
from rest_framework.views import APIView 
from rest_framework.response import Response

from .models import TicketLink
from collaboration import models
from project.serializer import User
from .models import Attachment, Ticket, TimeEntry 
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from .serializer import AttachmentSerializer, TicketSerializer, TimeEntrySerializer
from rest_framework import viewsets 
from rest_framework.decorators import action 
from  .serializer import TicketLinkSerializer
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
    

class ProjectTicketListView(ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer

    def get_queryset(self):
           project_id = self.kwargs['id']
           return Ticket.objects.filter(project_id=project_id).order_by('-created_at')
    
class TicketDetailView(RetrieveAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer
    lookup_field = 'id'  

    def get_queryset(self):
        
        return (
            Ticket.objects
            .select_related('project')
        )
    
class TicketUpdateView(UpdateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer
    lookup_field = 'id'

    def get_queryset(self): 
        return (
            Ticket.objects
            .select_related('project')
        ) 

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {"error": "status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = new_status
        ticket.save()

        return Response({
            "message": "Status updated",
            "ticket_id": ticket.id,
            "new_status": ticket.status
        })
    
    @action(detail=True, methods=['post'], url_path='labels')
    def add_label(self, request, pk=None):
        ticket = self.get_object()
        label_id = request.data.get('label_id')

        if not label_id:
            return Response({"error": "label_id required"}, status=400)

        try:
            label = Label.objects.get(id=label_id)
        except Label.DoesNotExist:
            return Response({"error": "Label not found"}, status=404)

        ticket.labels.add(label)

        return Response({
            "message": "Label added",
            "ticket_id": ticket.id,
            "label": label.name
        })

        def destroy(self, request, *args, **kwargs):
            ticket = self.get_object()
    
            # Example: permission rule
            if request.user != ticket.project.owner:
                return Response(
                    {"error": "Not allowed"},
                    status=status.HTTP_403_FORBIDDEN
                )
    
            ticket.delete()
            return Response({"message": "Ticket deleted"}, status=204)

class TicketassignmentView(APIView): 
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id): 
        ticket = Ticket.objects.get(id=id) 
        user_id = request.data.get('user_id') 
        user = User.objects.get(id=user_id) 
        ticket.assigned_to = user 
        ticket.save() 
        return Response({"message": "Ticket assigned successfully"}, status=200)
    def delete(self ,request, id ) :
        ticket = Ticket.objects.get(id=id) 
        ticket.assigned_to = None 
        ticket.save() 
        return Response({"message": "Ticket unassigned successfully"}, status=200) 
    def get(self, request, id): 
        ticket = Ticket.objects.get(id=id) 
        assigned_user = ticket.assigned_to 
        if assigned_user: 
            return Response({"assigned_to": assigned_user.username}, status=200) 
        else: 
            return Response({"assigned_to": None}, status=200)
class TicketTimeTrackingView(APIView): 
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, id): 
        ticket = Ticket.objects.get(id=id) 
        time_spent = request.data.get('time_spent') 
        if time_spent is not None: 
            ticket.time_spent += int(time_spent) 
            ticket.save() 
            return Response({"message": "Time tracked successfully"}, status=200) 
        else: 
            return Response({"error": "time_spent is required"}, status=400) 
    def get(self, request, id): 
        ticket = Ticket.objects.get(id=id) 
        return Response({"time_spent": ticket.time_spent}, status=200) 
    
    

class TicketTimeEntryCreateView(CreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TimeEntrySerializer

    def perform_create(self, serializer):
        ticket_id = self.kwargs['id']

        serializer.save(
            user=self.request.user,
            ticket_id=ticket_id
        )

class TicketTimeEntryListView(ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TimeEntrySerializer

    def get_queryset(self):
        ticket_id = self.kwargs['id']
        return TimeEntry.objects.filter(ticket_id=ticket_id).order_by('-created_at')    
    
class UserTimeEntryListView(ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TimeEntrySerializer

    def get_queryset(self):
        user_id = self.kwargs['id']
        return TimeEntry.objects.filter(user_id=user_id).order_by('-created_at')

class AttachmentCreateView(CreateAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = AttachmentSerializer

    def perform_create(self, serializer):
        ticket_id = self.kwargs['ticketId']
    
        serializer.save(
            ticket_id=ticket_id,
            uploaded_by=self.request.user
        )


class AttachmentListView(ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        ticket_id = self.kwargs['ticketId']
        return Attachment.objects.filter(ticket_id=ticket_id).order_by('-uploaded_at')
    
class AttachmentDeleteView(DestroyAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Attachment.objects.all()
    lookup_field = 'id'
class TicketLinkCreateView(CreateAPIView):
    authentication_classes = [JWTAuthentication ]
    permission_classes = [IsAuthenticated]
    serializer_class = TicketLinkSerializer

    def perform_create(self, serializer):
        source_id = self.kwargs['ticketId']

        serializer.save(
            source_ticket_id=source_id
        )

class TicketLinkListView(ListAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TicketLinkSerializer

    def get_queryset(self):
        ticket_id = self.kwargs['ticketId']

        return TicketLink.objects.filter(
            models.Q(source_ticket_id=ticket_id) |
            models.Q(target_ticket_id=ticket_id)
        )
class TicketLinkDeleteView(DestroyAPIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TicketLink.objects.all()
    lookup_field = 'id'