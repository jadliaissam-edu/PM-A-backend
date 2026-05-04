from rest_framework import permissions
from .models import ProjectMember, RoleName

class IsProjectMember(permissions.BasePermission):
    """
    Permission to only allow members of a project to access it.
    Expects 'project_id' or 'ticket_id' in view kwargs.
    """
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            # Try to get from ticket if available
            ticket_id = view.kwargs.get('ticket_id')
            if ticket_id:
                from tickets.models import Ticket
                try:
                    ticket = Ticket.objects.get(id=ticket_id)
                    project_id = ticket.project_id
                except Ticket.DoesNotExist:
                    return False
        
        if not project_id:
            return True # Let the view handle it or fall back to authenticated

        return ProjectMember.objects.filter(
            project_id=project_id, 
            user=request.user
        ).exists()

class IsProjectAdmin(permissions.BasePermission):
    """
    Permission to only allow project admins to access.
    """
    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False

        return ProjectMember.objects.filter(
            project_id=project_id, 
            user=request.user,
            role=RoleName.ADMIN
        ).exists()
