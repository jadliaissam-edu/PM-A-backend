from django.contrib.auth import get_user_model
from django.db import connection, models
from django.db.models import Count, IntegerField, Prefetch, Value
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.authentication import JWTAuthentication

from orgs.models import Organization, Workspace
from orgs.serializers import OrganizationTreeSerializer

from .models import (
    BoardColumn,
    Project,
    ProjectBoard,
    ProjectDashboard,
    ProjectMember,
    ProgressReport,
    Release,
    RoleName,
    Sprint,
    SprintReport,
    VelocityChart,
    BurndownChart,
    ProjectDocument,
    ProjectFile,
)
from .permissions import IsProjectMember, IsProjectAdmin
from .serializer import (
    BoardColumnSerializer,
    BoardConfigSerializer,
    CurrentUserProfileSerializer,
    ProjectBoardSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
    SprintSerializer,
    ReleaseSerializer,
    ProjectDocumentSerializer,
    ProjectFileSerializer,
)
from activity.utils import log_activity
from activity.emails import send_project_invitation_email


User = get_user_model()


DEFAULT_BOARD_COLUMNS = [
    {"name": "To Do", "position": 1, "wip_limit": 0, "is_done_column": False},
    {"name": "In Progress", "position": 2, "wip_limit": 0, "is_done_column": False},
    {"name": "Done", "position": 3, "wip_limit": 0, "is_done_column": True},
]


def base_project_queryset(user=None):
    annotations = {"member_count": Count("members", distinct=True)}
    if "tickets_ticket" in connection.introspection.table_names():
        annotations["ticket_count"] = Count("tickets", distinct=True)
    else:
        annotations["ticket_count"] = Value(0, output_field=IntegerField())

    queryset = Project.objects.select_related("workspace__organization").prefetch_related("members__user")
    
    if user:
        queryset = queryset.filter(members__user=user)

    return (
        queryset
        .annotate(**annotations)
        .order_by("-created_at")
    )


def ensure_board(project):
    board, _ = ProjectBoard.objects.get_or_create(project=project)
    if not board.columns.exists():
        BoardColumn.objects.bulk_create(
            [BoardColumn(board=board, **column) for column in DEFAULT_BOARD_COLUMNS]
        )
    return board


def ensure_project_dashboard(project):
    ProjectDashboard.objects.get_or_create(project=project)


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})


class CurrentUserProfileView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserProfileSerializer(request.user)
        return Response(
            {
                "id": request.user.id,
                **serializer.data,
            }
        )

    def patch(self, request):
        serializer = CurrentUserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Profile updated successfully", "user": serializer.data})


class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )


class UserListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        
        # Comprehensive queryset: users who share a workspace with the current user
        # We look at shared workspaces via WorkspaceMember OR shared projects
        from orgs.models import WorkspaceMember
        
        user_workspaces = WorkspaceMember.objects.filter(user=request.user).values_list('workspace_id', flat=True)
        user_project_workspaces = request.user.project_memberships.values_list('project__workspace_id', flat=True)
        
        all_workspace_ids = set(list(user_workspaces) + list(user_project_workspaces))
        
        queryset = User.objects.filter(
            models.Q(workspace_memberships__workspace_id__in=all_workspace_ids) |
            models.Q(project_memberships__project__workspace_id__in=all_workspace_ids)
        ).distinct()

        if organization_id:
            queryset = queryset.filter(
                models.Q(workspace_memberships__workspace__organization_id=organization_id) |
                models.Q(project_memberships__project__workspace__organization_id=organization_id)
            ).distinct()

        users = queryset.order_by("username")
        return Response(
            [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
                for user in users
            ]
        )


class DashboardView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        
        projects_qs = base_project_queryset(user=request.user)
        orgs_qs = Organization.objects.filter(workspaces__projects__members__user=request.user).distinct()
        workspaces_qs = Workspace.objects.filter(projects__members__user=request.user).distinct()
        projects_base_qs = Project.objects.filter(members__user=request.user).distinct()

        if organization_id:
            projects_qs = projects_qs.filter(workspace__organization_id=organization_id)
            orgs_qs = orgs_qs.filter(id=organization_id)
            workspaces_qs = workspaces_qs.filter(organization_id=organization_id)
            projects_base_qs = projects_base_qs.filter(workspace__organization_id=organization_id)

        projects = list(projects_qs[:6])
        organizations = orgs_qs.prefetch_related(
            Prefetch(
                "workspaces",
                queryset=Workspace.objects.filter(projects__members__user=request.user).prefetch_related(
                    Prefetch("projects", queryset=base_project_queryset(user=request.user))
                ).distinct().order_by("name"),
            )
        ).order_by("name")

        response = {
            "summary": {
                "organizations": orgs_qs.count(),
                "workspaces": workspaces_qs.count(),
                "projects": projects_base_qs.count(),
                "active_projects": projects_base_qs.filter(status="active").count(),
                "archived_projects": projects_base_qs.filter(status="archived").count(),
                "closed_projects": projects_base_qs.filter(status="closed").count(),
            },
            "recent_projects": ProjectSerializer(projects, many=True).data,
            "organizations": OrganizationTreeSerializer(organizations, many=True).data,
        }
        return Response(response)


class DashboardStatsView(DashboardView):
    def get(self, request):
        dashboard = super().get(request)
        return Response(dashboard.data["summary"])


class RecentProjectsView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        projects = base_project_queryset(user=request.user)
        if organization_id:
            projects = projects.filter(workspace__organization_id=organization_id)
        projects = projects[:6]
        return Response(ProjectSerializer(projects, many=True).data)


class DashboardProjectsView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = base_project_queryset(user=request.user)
        return Response(ProjectSerializer(projects, many=True).data)


class ProjectListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = base_project_queryset(user=request.user)

        workspace_id = request.query_params.get("workspace_id")
        organization_id = request.query_params.get("organization_id")
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")

        if workspace_id:
            projects = projects.filter(workspace_id=workspace_id)
        if organization_id:
            projects = projects.filter(workspace__organization_id=organization_id)
        if status_filter:
            projects = projects.filter(status=status_filter)
        if search:
            projects = projects.filter(name__icontains=search)

        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        ensure_board(project)
        ensure_project_dashboard(project)
        ProjectMember.objects.get_or_create(
            project=project,
            user=request.user,
            defaults={"role": RoleName.ADMIN},
        )
        
        # Also ensure membership in the workspace
        if project.workspace:
            from orgs.models import WorkspaceMember
            WorkspaceMember.objects.get_or_create(
                workspace=project.workspace,
                user=request.user,
                defaults={"role": "Admin"}
            )

        project = base_project_queryset().get(id=project.id)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsProjectMember]

    def get_project(self, request, project_id):
        return get_object_or_404(base_project_queryset(user=request.user), id=project_id)

    def get(self, request, project_id):
        project = self.get_project(request, project_id)
        return Response(ProjectSerializer(project).data)

    def patch(self, request, project_id):
        project = self.get_project(request, project_id)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        project.refresh_from_db()
        project = self.get_project(request, project_id)
        return Response(ProjectSerializer(project).data)

    def delete(self, request, project_id):
        project = self.get_project(request, project_id)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationReleaseListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_id = request.query_params.get("organization_id")
        if not organization_id:
            # Fallback to all projects if no org_id (though org context is preferred)
            releases = Release.objects.all().select_related("project").order_by("-target_date")[:10]
        else:
            releases = Release.objects.filter(
                project__workspace__organization_id=organization_id
            ).select_related("project").order_by("-target_date")
        
        return Response(ReleaseSerializer(releases, many=True).data)


class ProjectArchiveView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, members__user=request.user)
        project.status = "archived"
        project.save(update_fields=["status"])
        project = base_project_queryset(user=request.user).get(id=project.id)
        return Response(ProjectSerializer(project).data)


class ProjectCloseView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, members__user=request.user)
        project.status = "closed"
        project.save(update_fields=["status"])
        project = base_project_queryset(user=request.user).get(id=project.id)
        return Response(ProjectSerializer(project).data)


class ProjectMembersView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(
            Project.objects.filter(members__user=request.user).prefetch_related("members__user"), id=project_id
        )
        members = project.members.select_related("user").order_by("user__username")
        return Response(
            {
                "project_id": str(project.id),
                "members": ProjectMemberSerializer(members, many=True).data,
            }
        )

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        serializer = ProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member, _ = ProjectMember.objects.update_or_create(
            project=project,
            user=serializer.validated_data["user"],
            defaults={"role": serializer.validated_data["role"]},
        )
        return Response(
            ProjectMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectRoleListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(
            Project.objects.prefetch_related("members__user"), id=project_id
        )
        members = project.members.select_related("user").order_by("user__username")
        return Response(ProjectMemberSerializer(members, many=True).data)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        serializer = ProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership, created = ProjectMember.objects.update_or_create(
            project=project,
            user=serializer.validated_data["user"],
            defaults={"role": serializer.validated_data["role"]},
        )
        
        log_activity(
            actor=request.user,
            target=membership,
            action="role_change" if not created else "role_assign",
            description=f"{'Changed' if not created else 'Assigned'} role of {membership.user.username} to {membership.role}",
            project_id=project_id,
            new_value={"role": membership.role}
        )
        
        # Send Email Notification
        if created:
            send_project_invitation_email(
                recipient_email=membership.user.email,
                inviter_name=request.user.username,
                project_name=project.name,
                workspace_name=project.workspace.name if project.workspace else "General"
            )
        
        return Response(
            ProjectMemberSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectRoleDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, project_id, role_id):
        return get_object_or_404(ProjectMember.objects.select_related("user"), id=role_id, project_id=project_id)

    def patch(self, request, project_id, role_id):
        membership = self.get_object(project_id, role_id)
        old_role = membership.role
        serializer = ProjectMemberSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        log_activity(
            actor=request.user,
            target=membership,
            action="role_change",
            description=f"Changed role of {membership.user.username} from {old_role} to {membership.role}",
            project_id=project_id,
            old_value={"role": old_role},
            new_value={"role": membership.role}
        )
        
        return Response(ProjectMemberSerializer(membership).data)

    def delete(self, request, project_id, role_id):
        membership = self.get_object(project_id, role_id)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project.objects.select_related("workspace"), id=project_id)
        board = ensure_board(project)
        board = (
            ProjectBoard.objects.select_related("project")
            .prefetch_related("columns")
            .get(id=board.id)
        )
        return Response(
            {
                "project": ProjectSerializer(base_project_queryset().get(id=project.id)).data,
                "board": ProjectBoardSerializer(board).data,
            }
        )

    def patch(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        board = ensure_board(project)
        serializer = BoardConfigSerializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProjectBoardSerializer(board).data)


class BoardColumnCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        board = ensure_board(project)
        serializer = BoardColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        column = serializer.save(board=board)
        if "tickets_ticket" in connection.introspection.table_names():
            column = BoardColumn.objects.annotate(ticket_count=Count("tickets")).get(id=column.id)
        else:
            column.ticket_count = 0
        return Response(BoardColumnSerializer(column).data, status=status.HTTP_201_CREATED)


class BoardColumnDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_column(self, column_id):
        return get_object_or_404(BoardColumn, id=column_id)

    def patch(self, request, column_id, project_id=None):
        column = self.get_column(column_id)
        serializer = BoardColumnSerializer(column, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if "tickets_ticket" in connection.introspection.table_names():
            column = BoardColumn.objects.annotate(ticket_count=Count("tickets")).get(id=column.id)
        else:
            column.ticket_count = 0
        return Response(BoardColumnSerializer(column).data)

    def delete(self, request, column_id, project_id=None):
        column = self.get_column(column_id)
        column.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SprintListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsProjectMember]

    def get_board(self, project_id):
        project = get_object_or_404(Project, id=project_id)
        return ensure_board(project)

    def get(self, request, project_id):
        board = self.get_board(project_id)
        sprints = board.sprints.prefetch_related("reports").order_by("-start_date")
        return Response(SprintSerializer(sprints, many=True).data)

    def post(self, request, project_id):
        board = self.get_board(project_id)
        serializer = SprintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sprint = serializer.save(board=board)
        return Response(SprintSerializer(sprint).data, status=status.HTTP_201_CREATED)


class SprintDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, sprint_id):
        sprint = get_object_or_404(
            Sprint.objects.prefetch_related("reports"),
            id=sprint_id,
            board__project_id=project_id,
        )
        return Response(SprintSerializer(sprint).data)


class SprintReportView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, sprint_id):
        sprint = get_object_or_404(
            Sprint.objects.prefetch_related("reports"),
            id=sprint_id,
            board__project_id=project_id,
        )
        latest_report = sprint.reports.order_by("-id").first()
        if latest_report is None:
            return Response(
                {"error": "Sprint report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SprintSerializer(sprint).data["report"])


class SprintCompleteView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsProjectAdmin] # Only admins

    def post(self, request, project_id, sprint_id):
        sprint = get_object_or_404(Sprint, id=sprint_id, board__project_id=project_id)
        sprint.status = "closed"
        sprint.save(update_fields=["status"])
        
        # Calculate Analytics
        from tickets.models import Ticket, TicketStatus
        from django.db.models import Sum
        
        tickets = sprint.tickets.all()
        total_count = tickets.count()
        done_count = tickets.filter(status=TicketStatus.DONE).count()
        
        total_points = tickets.aggregate(Sum('estimate_story_points'))['estimate_story_points__sum'] or 0.0
        done_points = tickets.filter(status=TicketStatus.DONE).aggregate(Sum('estimate_story_points'))['estimate_story_points__sum'] or 0.0
        
        SprintReport.objects.update_or_create(
            sprint=sprint,
            defaults={
                "total_tickets": total_count,
                "done_tickets": done_count,
                "remaining_tickets": total_count - done_count,
                "completion_rate": (done_count / total_count * 100) if total_count > 0 else 0
            }
        )
        
        VelocityChart.objects.update_or_create(
            sprint=sprint,
            defaults={
                "data_json": {
                    "completed_points": done_points,
                    "planned_points": total_points,
                    "efficiency": (done_points / total_points * 100) if total_points > 0 else 0
                }
            }
        )
        
        BurndownChart.objects.update_or_create(
            sprint=sprint,
            defaults={
                "data_json": {
                    "start_points": total_points,
                    "end_points": total_points - done_points,
                    "points_history": [total_points, total_points - done_points] # Simplified 2-point history
                }
            }
        )
        
        log_activity(
            actor=request.user,
            target=sprint,
            action="sprint_complete",
            description=f"Completed sprint '{sprint.name}'",
            project_id=project_id,
            new_value={"status": "closed"}
        )
        
        return Response({"message": "Sprint closed.", "sprint": SprintSerializer(sprint).data})


class SprintStartView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, IsProjectAdmin] # Only admins

    def post(self, request, project_id, sprint_id):
        sprint = get_object_or_404(Sprint, id=sprint_id, board__project_id=project_id)
        sprint.status = "active"
        sprint.save(update_fields=["status"])
        
        log_activity(
            actor=request.user,
            target=sprint,
            action="sprint_start",
            description=f"Started sprint '{sprint.name}'",
            project_id=project_id,
            new_value={"status": "active"}
        )
        
        return Response({"message": "Sprint started.", "sprint": SprintSerializer(sprint).data})


class BoardConfigView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        board = ensure_board(project)
        serializer = BoardConfigSerializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BoardStatsView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        board = ensure_board(project)
        columns = board.columns.annotate(ticket_count=Count("tickets")).order_by("position")
        return Response(
            {
                "board_id": str(board.id),
                "total_columns": columns.count(),
                "total_tickets": sum(column.ticket_count for column in columns),
                "columns": [
                    {
                        "id": str(column.id),
                        "name": column.name,
                        "position": column.position,
                        "ticket_count": column.ticket_count,
                    }
                    for column in columns
                ],
            }
        )


class BoardTaskSummaryView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        summary = (
            Project.objects.filter(id=project_id)
            .values("tickets__status")
            .annotate(count=Count("tickets__id"))
            .order_by("tickets__status")
        )
        return Response(
            [
                {"status": row["tickets__status"], "count": row["count"]}
                for row in summary
                if row["tickets__status"] is not None
            ]
        )


class ProjectProgressReportView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        total = project.tickets.count()
        done = project.tickets.filter(status="done").count()
        completion_rate = (done / total * 100) if total else 0
        report = (
            ProgressReport.objects.filter(scope="project", scope_id=project.id)
            .order_by("-generated_at")
            .first()
        )
        return Response(
            {
                "project_id": str(project.id),
                "completion_rate": round(completion_rate, 2),
                "open_issues": total - done,
                "velocity": report.velocity if report else 0,
                "generated_at": report.generated_at if report else None,
            }
        )


class SprintProgressReportView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, sprint_id):
        sprint = get_object_or_404(Sprint, id=sprint_id, board__project_id=project_id)
        total = sprint.tickets.count()
        done = sprint.tickets.filter(status="done").count()
        completion_rate = (done / total * 100) if total else 0
        return Response(
            {
                "project_id": str(project_id),
                "sprint_id": str(sprint.id),
                "completion_rate": round(completion_rate, 2),
                "open_issues": total - done,
                "velocity": done,
            }
        )


class MemberProgressReportView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, user_id):
        tickets = Project.objects.get(id=project_id).tickets.filter(assignments__user_id=user_id).distinct()
        total = tickets.count()
        done = tickets.filter(status="done").count()
        hours = tickets.aggregate(total_hours=Count("time_entries"))["total_hours"] or 0
        completion_rate = (done / total * 100) if total else 0
        return Response(
            {
                "project_id": str(project_id),
                "user_id": user_id,
                "completion_rate": round(completion_rate, 2),
                "open_issues": total - done,
                "velocity": done,
                "activity_count": hours,
            }
        )

class ProjectDocumentListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        documents = ProjectDocument.objects.filter(project_id=project_id)
        return Response(ProjectDocumentSerializer(documents, many=True).data)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        serializer = ProjectDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(project=project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProjectDocumentDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, document_id):
        document = get_object_or_404(ProjectDocument, id=document_id, project_id=project_id)
        return Response(ProjectDocumentSerializer(document).data)

    def patch(self, request, project_id, document_id):
        document = get_object_or_404(ProjectDocument, id=document_id, project_id=project_id)
        serializer = ProjectDocumentSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, project_id, document_id):
        document = get_object_or_404(ProjectDocument, id=document_id, project_id=project_id)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectFileListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        files = ProjectFile.objects.filter(project_id=project_id).select_related("uploaded_by")
        return Response(ProjectFileSerializer(files, many=True).data)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        serializer = ProjectFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.save(project=project, uploaded_by=request.user)
        
        log_activity(
            actor=request.user,
            target=file_obj,
            action="file_upload",
            description=f"Uploaded file '{file_obj.file_name}' to project",
            project_id=project_id
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProjectFileDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, file_id):
        file_obj = get_object_or_404(ProjectFile, id=file_id, project_id=project_id)
        return Response(ProjectFileSerializer(file_obj).data)

    def delete(self, request, project_id, file_id):
        file_obj = get_object_or_404(ProjectFile, id=file_id, project_id=project_id)
        file_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectFromTemplateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    TEMPLATES = {
        "1": { # Scrum
            "columns": [
                {"name": "Backlog", "position": 1},
                {"name": "To Do", "position": 2},
                {"name": "In Progress", "position": 3},
                {"name": "Done", "position": 4, "is_done_column": True},
            ],
            "labels": ["sprint-goal", "tech-debt", "spike"]
        },
        "2": { # Kanban
            "columns": [
                {"name": "To Do", "position": 1},
                {"name": "In Progress", "position": 2},
                {"name": "Review", "position": 3},
                {"name": "Done", "position": 4, "is_done_column": True},
            ],
            "labels": ["blocked", "ready-for-review"]
        },
        "3": { # Bug Tracking
            "columns": [
                {"name": "New", "position": 1},
                {"name": "Assigned", "position": 2},
                {"name": "Fixing", "position": 3},
                {"name": "Validated", "position": 4, "is_done_column": True},
            ],
            "labels": ["security", "regression", "hotfix"]
        },
        "4": { # DevOps
            "columns": [
                {"name": "Planned", "position": 1},
                {"name": "Deploying", "position": 2},
                {"name": "Monitoring", "position": 3},
                {"name": "Completed", "position": 4, "is_done_column": True},
            ],
            "labels": ["prod", "staging", "pipeline-fail"]
        }
    }

    def post(self, request):
        template_id = str(request.data.get("template_id"))
        project_name = request.data.get("project_name")
        project_key = request.data.get("project_key", project_name[:4].upper() if project_name else "PROJ")
        workspace_id = request.data.get("workspace_id")
        
        if template_id not in self.TEMPLATES:
            return Response({"error": "Invalid template_id"}, status=status.HTTP_400_BAD_REQUEST)
        
        template = self.TEMPLATES[template_id]
        
        # Create Project
        project = Project.objects.create(
            name=project_name,
            key=project_key,
            workspace_id=workspace_id,
            status="active"
        )
        
        # Create Board
        board = ProjectBoard.objects.create(project=project)
        
        # Create Columns
        for col_data in template["columns"]:
            BoardColumn.objects.create(board=board, **col_data)
            
        # Create Dashboard
        ensure_project_dashboard(project)
        
        # Add Creator as Admin
        ProjectMember.objects.create(
            project=project,
            user=request.user,
            role=RoleName.ADMIN
        )
        
        log_activity(
            actor=request.user,
            target=project,
            action="project_created",
            description=f"Created project '{project_name}' from template {template_id}",
            project_id=project.id
        )
        
        return Response({
            "message": "Project created successfully from template",
            "project": ProjectSerializer(project).data
        }, status=status.HTTP_201_CREATED)
