from django.urls import path

from tickets.views import AttachmentCreateView, AttachmentDeleteView, AttachmentListView, ProjectTicketListView, TicketDetailView, TicketLinkDeleteView, TicketLinkListView, UserTimeEntryListView 
from tickets.views import TicketTimeEntryListView, TicketTimeEntryCreateView , TicketLinkCreateView
urlpatterns = [ 
    path('projects/<uuid:id>/tickets/', ProjectTicketListView.as_view()),
    path('tickets/<uuid:id>/', TicketDetailView.as_view()),
    path('tickets/<uuid:id>/time-entries/', TicketTimeEntryListView.as_view()),
    path('tickets/<uuid:id>/time-entries/create/', TicketTimeEntryCreateView.as_view()),
    path('users/<uuid:id>/time-entries/', UserTimeEntryListView.as_view()),   
    path('tickets/<uuid:ticketId>/attachments/', AttachmentListView.as_view()),
    path('tickets/<uuid:ticketId>/attachments/upload/', AttachmentCreateView.as_view()),
    path('attachments/<uuid:id>/', AttachmentDeleteView.as_view()),  
    path('tickets/<uuid:ticketId>/links/', TicketLinkListView.as_view()),
    path('tickets/<uuid:ticketId>/links/create/', TicketLinkCreateView.as_view()),
    path('ticket-links/<uuid:id>/', TicketLinkDeleteView.as_view()),
]


