from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.authentication import JWTAuthentication

from project.models import BoardColumn, Project, Release, Sprint

from .models import Attachment, BacklogItem, Ticket, TicketAssignment, TicketLink, TicketMovement, TimeEntry
from .models import TicketAuditLog
from project.serializer import ReleaseSerializer
from project.permissions import IsProjectMember, IsProjectAdmin
from .serializer import (
    AttachmentSerializer,
    BacklogItemSerializer,
    TicketAssignmentSerializer,
    TicketLinkSerializer,
    TicketSerializer,
    TimeEntrySerializer,
    TicketAuditLogSerializer,
)
from activity.utils import log_activity


class GlobalTicketListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        workspace_id = request.query_params.get("workspace_id")
        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")
        search = request.query_params.get("search") or request.query_params.get("q")

        tickets = (
            Ticket.objects.filter(project__members__user=request.user)
            .select_related("project__workspace__organization", "current_column", "sprint", "release")
            .prefetch_related("assignments__user")
            .order_by("-created_at")
        )

        if organization_id:
            tickets = tickets.filter(project__workspace__organization_id=organization_id)
        if workspace_id:
            tickets = tickets.filter(project__workspace_id=workspace_id)
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        if priority_filter:
            tickets = tickets.filter(priority=priority_filter)
        if search:
            tickets = tickets.filter(
                Q(title__icontains=search)
                | Q(description_markdown__icontains=search)
                | Q(labels__icontains=search)
                | Q(assignments__user__username__icontains=search)
            ).distinct()

        return Response(TicketSerializer(tickets, many=True).data)




def get_project(project_id):
    return get_object_or_404(Project, id=project_id)


def get_project_ticket(project_id, ticket_id):
    return get_object_or_404(
        Ticket.objects.select_related("project", "current_column", "sprint", "release").prefetch_related("assignments__user"),
        id=ticket_id,
        project_id=project_id,
    )

class AuthenticatedAPIView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsProjectMember] # Apply by default to project views

class ProjectTicketListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id):
        tickets = (
            Ticket.objects.filter(project_id=project_id)
            .select_related("current_column", "sprint", "release")
            .prefetch_related("assignments__user")
            .order_by("-created_at")
        )
        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")
        sprint_id = request.query_params.get("sprint_id")
        release_id = request.query_params.get("release_id")
        search = request.query_params.get("search") or request.query_params.get("q")

        if status_filter:
            tickets = tickets.filter(status=status_filter)
        if priority_filter:
            tickets = tickets.filter(priority=priority_filter)
        if sprint_id:
            tickets = tickets.filter(sprint_id=sprint_id)
        if release_id:
            tickets = tickets.filter(release_id=release_id)
        if search:
            tickets = tickets.filter(
                Q(title__icontains=search)
                | Q(description_markdown__icontains=search)
                | Q(labels__icontains=search)
                | Q(assignments__user__username__icontains=search)
            ).distinct()

        return Response(TicketSerializer(tickets, many=True).data)

    def post(self, request, project_id):
        project = get_project(project_id)
        serializer = TicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save(project=project)
        try:
            TicketAuditLog.objects.create(ticket=ticket, actor_user=request.user, field_name='created', old_value='', new_value=f"title={ticket.title}")
        except Exception:
            pass
        
        log_activity(
            actor=request.user,
            target=ticket,
            action="ticket_create",
            description=f"Created ticket '{ticket.title}'",
            project_id=project_id,
            new_value={"title": ticket.title, "status": ticket.status}
        )

        ticket = get_project_ticket(project_id, ticket.id)
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)


class TicketDetailView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        return Response(TicketSerializer(ticket).data)

    def patch(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        serializer = TicketSerializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        # capture before values
        before = {f: getattr(ticket, f) for f in ['title', 'description_markdown', 'type', 'priority', 'status', 'labels']}
        updated = serializer.save()
        # create audit logs for changed fields
        for f in before:
            old = before[f]
            new = getattr(updated, f)
            if old != new:
                try:
                    TicketAuditLog.objects.create(ticket=updated, actor_user=request.user, field_name=f, old_value=str(old), new_value=str(new))
                except Exception:
                    pass
        ticket = get_project_ticket(project_id, ticket_id)
        return Response(TicketSerializer(ticket).data)

    def delete(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketStatusView(AuthenticatedAPIView):
    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        old_status = ticket.status
        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "status is required"}, status=status.HTTP_400_BAD_REQUEST)
        ticket.status = new_status
        ticket.save(update_fields=["status"])
        
        log_activity(
            actor=request.user,
            target=ticket,
            action="status_change",
            description=f"Changed status of ticket '{ticket.title}' from {old_status} to {new_status}",
            project_id=project_id,
            old_value={"status": old_status},
            new_value={"status": new_status}
        )
        return Response({"message": "Status updated", "ticket": TicketSerializer(ticket).data})
        try:
            TicketAuditLog.objects.create(ticket=ticket, actor_user=request.user, field_name='status', old_value=old_status, new_value=new_status)
        except Exception:
            pass


class TicketLabelsView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        return Response({"labels": ticket.labels})

    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        action = request.data.get("action", "add")
        labels_input = request.data.get("labels")
        
        if labels_input is None:
            single_label = request.data.get("label")
            labels_input = [single_label] if single_label else []
            
        if not isinstance(labels_input, list):
            labels_input = [labels_input]
            
        current_labels = list(ticket.labels) if isinstance(ticket.labels, list) else []
        
        if action == "set":
            current_labels = labels_input
        elif action == "remove":
            current_labels = [l for l in current_labels if l not in labels_input]
        else: # add
            for label in labels_input:
                if label and label not in current_labels:
                    current_labels.append(label)
        
        ticket.labels = current_labels
        ticket.save(update_fields=["labels"])
        try:
            TicketAuditLog.objects.create(ticket=ticket, actor_user=request.user, field_name='labels', old_value=str(current_labels), new_value=str(ticket.labels))
        except Exception:
            pass
        return Response({
            "message": f"Labels updated ({action})", 
            "labels": ticket.labels,
            "ticket": TicketSerializer(ticket).data
        })


class TicketAssigneeListCreateView(AuthenticatedAPIView):
    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        user_id = request.data.get("user") or request.data.get("user_id")
        if not user_id:
            return Response({"error": "user is required"}, status=status.HTTP_400_BAD_REQUEST)
        assignment, _ = TicketAssignment.objects.get_or_create(ticket=ticket, user_id=user_id)
        return Response(TicketAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    def get(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        assignments = ticket.assignments.select_related("user").order_by("assigned_at")
        return Response(TicketAssignmentSerializer(assignments, many=True).data)


class TicketAssigneeDeleteView(AuthenticatedAPIView):
    def delete(self, request, project_id, ticket_id, user_id):
        ticket = get_project_ticket(project_id, ticket_id)
        TicketAssignment.objects.filter(ticket=ticket, user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketTimeEntryListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        entries = ticket.time_entries.select_related("user").order_by("-started_at")
        return Response(TimeEntrySerializer(entries, many=True).data)

    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        serializer = TimeEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save(ticket=ticket, user=request.user)
        return Response(TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class TicketAttachmentListCreateView(AuthenticatedAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        attachments = ticket.attachments.select_related("uploaded_by").order_by("-uploaded_at")
        return Response(AttachmentSerializer(attachments, many=True).data)

    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        # Handle file upload from multipart form. Expect field name 'file'.
        upload = request.FILES.get('file') or request.FILES.get('attachment')
        if not upload:
            # Fallback to serializer-based creation if client provides file_url metadata
            serializer = AttachmentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            attachment = serializer.save(ticket=ticket, uploaded_by=request.user)
            return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)

        # Save uploaded file to default storage under media/attachments/<ticket_id>/
        from django.core.files.storage import default_storage
        from django.conf import settings
        import os
        rel_dir = os.path.join('attachments', str(ticket.id))
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, rel_dir)):
            try:
                os.makedirs(os.path.join(settings.MEDIA_ROOT, rel_dir), exist_ok=True)
            except Exception:
                pass

        filename = upload.name
        storage_path = default_storage.save(os.path.join(rel_dir, filename), upload)
        file_url = (settings.MEDIA_URL.rstrip('/') + '/' + storage_path).lstrip('/')

        attachment = Attachment.objects.create(
            ticket=ticket,
            uploaded_by=request.user,
            file_name=upload.name,
            file_url=file_url,
            mime_type=getattr(upload, 'content_type', ''),
            file_size=getattr(upload, 'size', 0),
        )
        return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class TicketAttachmentDeleteView(AuthenticatedAPIView):
    def delete(self, request, project_id, ticket_id, attachment_id):
        attachment = get_object_or_404(Attachment, id=attachment_id, ticket_id=ticket_id, ticket__project_id=project_id)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketLinkListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        links = TicketLink.objects.filter(source_ticket_id=ticket_id, source_ticket__project_id=project_id).select_related("target_ticket")
        return Response(TicketLinkSerializer(links, many=True).data)

    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        serializer = TicketLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = serializer.save(source_ticket=ticket)
        return Response(TicketLinkSerializer(link).data, status=status.HTTP_201_CREATED)


class TicketLinkDeleteView(AuthenticatedAPIView):
    def delete(self, request, project_id, ticket_id, link_id):
        link = get_object_or_404(TicketLink, id=link_id, source_ticket_id=ticket_id, source_ticket__project_id=project_id)
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TicketMoveView(AuthenticatedAPIView):
    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        to_column = get_object_or_404(BoardColumn, id=request.data.get("to_column"), board__project_id=project_id)
        from_column = ticket.current_column
        ticket.current_column = to_column
        ticket.status = request.data.get("status", ticket.status)
        ticket.save(update_fields=["current_column", "status"])
        movement = TicketMovement.objects.create(
            ticket=ticket,
            from_column=from_column,
            to_column=to_column,
            moved_by=request.user,
        )
        
        log_activity(
            actor=request.user,
            target=ticket,
            action="ticket_move",
            description=f"Moved ticket '{ticket.title}' from '{from_column.name if from_column else 'N/A'}' to '{to_column.name}'",
            project_id=project_id,
            old_value={"column": from_column.name if from_column else None},
            new_value={"column": to_column.name}
        )
        
        return Response(
            {
                "message": "Ticket moved",
                "movement_id": movement.id,
                "ticket": TicketSerializer(ticket).data,
            }
        )


class TicketMovementListView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        movements = (
            TicketMovement.objects.filter(ticket_id=ticket_id, ticket__project_id=project_id)
            .select_related("from_column", "to_column", "moved_by")
            .order_by("-moved_at")
        )
        payload = [
            {
                "id": str(movement.id),
                "from_column": movement.from_column.name if movement.from_column else None,
                "to_column": movement.to_column.name if movement.to_column else None,
                "moved_by": movement.moved_by.username if movement.moved_by else None,
                "moved_at": movement.moved_at,
            }
            for movement in movements
        ]
        return Response(payload)


class TicketAuditLogListView(AuthenticatedAPIView):
    def get(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        logs = ticket.audit_logs.select_related('actor_user').order_by('-changed_at')
        return Response(TicketAuditLogSerializer(logs, many=True).data)


class BacklogListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id):
        items = (
            BacklogItem.objects.filter(project_id=project_id)
            .select_related("ticket")
            .prefetch_related("ticket__assignments__user")
            .order_by("rank", "created_at")
        )
        return Response(BacklogItemSerializer(items, many=True).data)

    def post(self, request, project_id):
        project = get_project(project_id)
        serializer = BacklogItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(project=project)
        item = BacklogItem.objects.select_related("ticket").get(id=item.id)
        return Response(BacklogItemSerializer(item).data, status=status.HTTP_201_CREATED)


class BacklogPrioritizeView(AuthenticatedAPIView):
    def patch(self, request, project_id, backlog_item_id):
        item = get_object_or_404(BacklogItem, id=backlog_item_id, project_id=project_id)
        if "rank" in request.data:
            item.rank = request.data["rank"]
        if "priority_score" in request.data:
            item.priority_score = request.data["priority_score"]
        item.save(update_fields=["rank", "priority_score"])
        return Response(BacklogItemSerializer(item).data)


class BacklogAddToSprintView(AuthenticatedAPIView):
    def post(self, request, project_id, backlog_item_id):
        item = get_object_or_404(BacklogItem, id=backlog_item_id, project_id=project_id)
        sprint = get_object_or_404(Sprint, id=request.data.get("sprint_id"), board__project_id=project_id)
        item.ticket.sprint = sprint
        item.ticket.save(update_fields=["sprint"])
        return Response({"message": "Ticket added to sprint", "ticket": TicketSerializer(item.ticket).data})


class BacklogDeleteView(AuthenticatedAPIView):
    def delete(self, request, project_id, backlog_item_id):
        item = get_object_or_404(BacklogItem, id=backlog_item_id, project_id=project_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReleaseListCreateView(AuthenticatedAPIView):
    def get(self, request, project_id):
        releases = Release.objects.filter(project_id=project_id).order_by("-target_date")
        return Response(ReleaseSerializer(releases, many=True).data)

    def post(self, request, project_id):
        project = get_project(project_id)
        serializer = ReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        release = serializer.save(
            project=project, 
            created_by=request.user, 
            modified_by=request.user
        )
        return Response(ReleaseSerializer(release).data, status=status.HTTP_201_CREATED)


class ReleaseDetailView(AuthenticatedAPIView):
    def get_object(self, project_id, release_id):
        return get_object_or_404(Release, id=release_id, project_id=project_id)

    def get(self, request, project_id, release_id):
        release = self.get_object(project_id, release_id)
        return Response(ReleaseSerializer(release).data)

    def patch(self, request, project_id, release_id):
        release = self.get_object(project_id, release_id)
        for field in ["tag", "target_date", "description", "status"]:
            if field in request.data:
                setattr(release, field, request.data[field])
        release.save()
        return self.get(request, project_id, release_id)

    def delete(self, request, project_id, release_id):
        release = self.get_object(project_id, release_id)
        release.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReleaseCloseView(AuthenticatedAPIView):
    def post(self, request, project_id, release_id):
        release = get_object_or_404(Release, id=release_id, project_id=project_id)
        release.status = "released"
        release.save(update_fields=["status"])
        return Response({"message": "Release closed", "status": release.status})


class BulkAssignReleaseView(AuthenticatedAPIView):
    """Assign or unassign multiple tickets to a release in a project.

    POST body: { "ticket_ids": ["uuid", ...] }
    If the view is mounted under a release URL (projects/<project_id>/releases/<release_id>/assign-tickets/)
    the release is taken from the URL. Otherwise, include `release_id` in the body (or send null to unassign).
    """
    def post(self, request, project_id, release_id=None):
        ticket_ids = request.data.get("ticket_ids") or request.data.get("tickets")
        if not ticket_ids or not isinstance(ticket_ids, list):
            return Response({"error": "ticket_ids (list) is required"}, status=status.HTTP_400_BAD_REQUEST)

        release = None
        if release_id:
            release = get_object_or_404(Release, id=release_id, project_id=project_id)
        else:
            body_rel = request.data.get("release_id") if "release_id" in request.data else None
            if body_rel:
                release = get_object_or_404(Release, id=body_rel, project_id=project_id)

        # Restrict to tickets within the project
        tickets_qs = Ticket.objects.filter(id__in=ticket_ids, project_id=project_id)
        tickets_qs.update(release=release)

        updated = (
            Ticket.objects.filter(id__in=ticket_ids, project_id=project_id)
            .select_related("release", "sprint", "current_column")
            .prefetch_related("assignments__user")
        )

        # Log activity for each updated ticket
        for t in updated:
            try:
                log_activity(
                    actor=request.user,
                    target=t,
                    action="assign_release",
                    description=f"Assigned to release {release.tag if release else 'Unassigned'}",
                    project_id=project_id,
                    new_value={"release": str(release.id) if release else None},
                )
            except Exception:
                # Do not fail the whole request for logging issues
                pass

        return Response(TicketSerializer(updated, many=True).data)


class ReleaseDashboardView(AuthenticatedAPIView):
    def get(self, request, project_id, release_id):
        release = get_object_or_404(Release, id=release_id, project_id=project_id)
        total = Ticket.objects.filter(project_id=project_id, release=release).count()
        resolved = Ticket.objects.filter(project_id=project_id, release=release, status="done").count()
        remaining = total - resolved
        progress = (resolved / total * 100) if total else 0
        return Response(
            {
                "release_id": str(release.id),
                "progress_percent": round(progress, 2),
                "resolved_issues": resolved,
                "remaining_issues": remaining,
            }
        )


class ReleaseIssuesSummaryView(AuthenticatedAPIView):
    def get(self, request, project_id, release_id):
        summary = (
            Ticket.objects.filter(project_id=project_id, release_id=release_id)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        return Response(list(summary))


class TicketImportView(AuthenticatedAPIView):
    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        import_format = request.data.get('format', 'csv')
        source_file = request.FILES.get('file')
        
        if not source_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file temporarily
        from django.core.files.storage import default_storage
        file_path = f"imports/{project_id}_{source_file.name}"
        path = default_storage.save(file_path, source_file)
        
        from .models import TicketImportJob, ImportFormat
        job = TicketImportJob.objects.create(
            project=project,
            format=import_format,
            source_file_url=path,
            status='pending'
        )
        
        # Process synchronously for now
        from .importers import process_ticket_import_job
        process_ticket_import_job(job.id)
        
        job.refresh_from_db()
        return Response({
            "job_id": job.id,
            "status": job.status,
            "message": "Import processed" if job.status == 'success' else "Import failed"
        })
