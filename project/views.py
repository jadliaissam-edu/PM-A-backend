from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Count, IntegerField, Prefetch, Value
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

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
)
from .serializer import (
    BoardColumnSerializer,
    BoardConfigSerializer,
    CurrentUserProfileSerializer,
    ProjectBoardSerializer,
    ProjectMemberSerializer,
    ProjectSerializer,
    SprintSerializer,
)


User = get_user_model()


DEFAULT_BOARD_COLUMNS = [
    {"name": "To Do", "position": 1, "wip_limit": 0, "is_done_column": False},
    {"name": "In Progress", "position": 2, "wip_limit": 0, "is_done_column": False},
    {"name": "Done", "position": 3, "wip_limit": 0, "is_done_column": True},
]


def base_project_queryset():
    annotations = {"member_count": Count("members", distinct=True)}
    if "tickets_ticket" in connection.introspection.table_names():
        annotations["ticket_count"] = Count("tickets", distinct=True)
    else:
        annotations["ticket_count"] = Value(0, output_field=IntegerField())

    return (
        Project.objects.select_related("workspace__organization")
        .prefetch_related("members__user")
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


class DashboardView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = list(base_project_queryset()[:6])
        organizations = Organization.objects.prefetch_related(
            Prefetch(
                "workspaces",
                queryset=Workspace.objects.prefetch_related(
                    Prefetch("projects", queryset=base_project_queryset())
                ).order_by("name"),
            )
        ).order_by("name")

        response = {
            "summary": {
                "organizations": Organization.objects.count(),
                "workspaces": Workspace.objects.count(),
                "projects": Project.objects.count(),
                "active_projects": Project.objects.filter(status="active").count(),
                "archived_projects": Project.objects.filter(status="archived").count(),
                "closed_projects": Project.objects.filter(status="closed").count(),
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
        projects = base_project_queryset()[:6]
        return Response(ProjectSerializer(projects, many=True).data)


class DashboardProjectsView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = base_project_queryset()
        return Response(ProjectSerializer(projects, many=True).data)


class ProjectListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = base_project_queryset()

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

        project = base_project_queryset().get(id=project.id)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_project(self, project_id):
        return get_object_or_404(base_project_queryset(), id=project_id)

    def get(self, request, project_id):
        project = self.get_project(project_id)
        return Response(ProjectSerializer(project).data)

    def patch(self, request, project_id):
        project = self.get_project(project_id)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        project.refresh_from_db()
        project = self.get_project(project_id)
        return Response(ProjectSerializer(project).data)

    def delete(self, request, project_id):
        project = self.get_project(project_id)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectArchiveView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        project.status = "archived"
        project.save(update_fields=["status"])
        project = base_project_queryset().get(id=project.id)
        return Response(ProjectSerializer(project).data)


class ProjectCloseView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        project.status = "closed"
        project.save(update_fields=["status"])
        project = base_project_queryset().get(id=project.id)
        return Response(ProjectSerializer(project).data)


class ProjectMembersView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(
            Project.objects.prefetch_related("members__user"), id=project_id
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
        membership, _ = ProjectMember.objects.update_or_create(
            project=project,
            user=serializer.validated_data["user"],
            defaults={"role": serializer.validated_data["role"]},
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
        serializer = ProjectMemberSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, sprint_id):
        sprint = get_object_or_404(Sprint, id=sprint_id, board__project_id=project_id)
        sprint.status = "closed"
        sprint.save(update_fields=["status"])
        return Response({"message": "Sprint closed.", "sprint": SprintSerializer(sprint).data})


class SprintStartView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id, sprint_id):
        sprint = get_object_or_404(Sprint, id=sprint_id, board__project_id=project_id)
        sprint.status = "active"
        sprint.save(update_fields=["status"])
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
