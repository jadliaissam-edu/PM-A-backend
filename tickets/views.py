from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from project.models import BoardColumn, Project, Release, Sprint

from .models import Attachment, BacklogItem, Ticket, TicketAssignment, TicketLink, TicketMovement, TimeEntry
from .serializer import (
    AttachmentSerializer,
    BacklogItemSerializer,
    TicketAssignmentSerializer,
    TicketLinkSerializer,
    TicketSerializer,
    TimeEntrySerializer,
)


class AuthenticatedAPIView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


def get_project(project_id):
    return get_object_or_404(Project, id=project_id)


def get_project_ticket(project_id, ticket_id):
    return get_object_or_404(
        Ticket.objects.select_related("project", "current_column", "sprint", "release").prefetch_related("assignments__user"),
        id=ticket_id,
        project_id=project_id,
    )


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
        search = request.query_params.get("search")

        if status_filter:
            tickets = tickets.filter(status=status_filter)
        if priority_filter:
            tickets = tickets.filter(priority=priority_filter)
        if sprint_id:
            tickets = tickets.filter(sprint_id=sprint_id)
        if release_id:
            tickets = tickets.filter(release_id=release_id)
        if search:
            tickets = tickets.filter(title__icontains=search)

        return Response(TicketSerializer(tickets, many=True).data)

    def post(self, request, project_id):
        project = get_project(project_id)
        serializer = TicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save(project=project)
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
        serializer.save()
        ticket = get_project_ticket(project_id, ticket_id)
        return Response(TicketSerializer(ticket).data)


class TicketStatusView(AuthenticatedAPIView):
    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "status is required"}, status=status.HTTP_400_BAD_REQUEST)
        ticket.status = new_status
        ticket.save(update_fields=["status"])
        return Response({"message": "Status updated", "ticket": TicketSerializer(ticket).data})


class TicketLabelsView(AuthenticatedAPIView):
    def post(self, request, project_id, ticket_id):
        ticket = get_project_ticket(project_id, ticket_id)
        labels = request.data.get("labels")
        if labels is None:
            single_label = request.data.get("label")
            labels = [single_label] if single_label else []
        ticket.labels = labels
        ticket.save(update_fields=["labels"])
        return Response({"message": "Labels updated", "ticket": TicketSerializer(ticket).data})


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
        serializer = AttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(ticket=ticket, uploaded_by=request.user)
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
        payload = [
            {
                "id": str(release.id),
                "tag": release.tag,
                "target_date": release.target_date,
                "description": release.description,
                "status": release.status,
            }
            for release in releases
        ]
        return Response(payload)

    def post(self, request, project_id):
        project = get_project(project_id)
        release = Release.objects.create(
            project=project,
            tag=request.data["tag"],
            target_date=request.data["target_date"],
            description=request.data.get("description", ""),
            status=request.data.get("status", "planned"),
        )
        return Response(
            {
                "id": str(release.id),
                "tag": release.tag,
                "target_date": release.target_date,
                "description": release.description,
                "status": release.status,
            },
            status=status.HTTP_201_CREATED,
        )


class ReleaseDetailView(AuthenticatedAPIView):
    def get_object(self, project_id, release_id):
        return get_object_or_404(Release, id=release_id, project_id=project_id)

    def get(self, request, project_id, release_id):
        release = self.get_object(project_id, release_id)
        return Response(
            {
                "id": str(release.id),
                "tag": release.tag,
                "target_date": release.target_date,
                "description": release.description,
                "status": release.status,
            }
        )

    def patch(self, request, project_id, release_id):
        release = self.get_object(project_id, release_id)
        for field in ["tag", "target_date", "description", "status"]:
            if field in request.data:
                setattr(release, field, request.data[field])
        release.save()
        return self.get(request, project_id, release_id)


class ReleaseCloseView(AuthenticatedAPIView):
    def post(self, request, project_id, release_id):
        release = get_object_or_404(Release, id=release_id, project_id=project_id)
        release.status = "released"
        release.save(update_fields=["status"])
        return Response({"message": "Release closed", "status": release.status})


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
