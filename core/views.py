from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import BoardColumn, Project, ProjectBoard, Role
from .serializer import (
    BoardColumnSerializer,
    CurrentUserProfileSerializer,
    ProjectSerializer,
    RoleSerializer,
)


User = get_user_model()


def project_membership_q(user):
    return Q(owner=user) | Q(roles__user=user)


def can_access_project(user, project):
    return project.owner_id == user.id or project.roles.filter(user=user).exists()


def ensure_board(project):
    board, _ = ProjectBoard.objects.get_or_create(project=project)
    return board


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})


class CurrentUserProfileView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        )

    def patch(self, request):
        user = request.user
        serializer = CurrentUserProfileSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user.username = serializer.validated_data.get('username', user.username)
        user.email = serializer.validated_data.get('email', user.email)
        user.first_name = serializer.validated_data.get('first_name', user.first_name)
        user.last_name = serializer.validated_data.get('last_name', user.last_name)
        user.save()
        return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        )


class DashboardView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(project_membership_q(request.user)).distinct()[:5]
        return Response(
            {
                'total_projects': Project.objects.filter(project_membership_q(request.user)).distinct().count(),
                'owned_projects': Project.objects.filter(owner=request.user).count(),
                'member_projects': Project.objects.filter(roles__user=request.user).distinct().count(),
                'archived_projects': Project.objects.filter(project_membership_q(request.user), is_archived=True).distinct().count(),
                'recent_projects': ProjectSerializer(projects, many=True).data,
            }
        )


class DashboardStatsView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                'total_projects': Project.objects.filter(project_membership_q(request.user)).distinct().count(),
                'owned_projects': Project.objects.filter(owner=request.user).count(),
                'member_projects': Project.objects.filter(roles__user=request.user).distinct().count(),
                'archived_projects': Project.objects.filter(project_membership_q(request.user), is_archived=True).distinct().count(),
                'recent_projects': ProjectSerializer(
                    Project.objects.filter(project_membership_q(request.user)).distinct()[:5],
                    many=True,
                ).data,
            }
        )


class RecentProjectsView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(project_membership_q(request.user)).distinct()[:5]
        return Response(ProjectSerializer(projects, many=True).data)


class ProjectListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(project_membership_q(request.user)).distinct()
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(owner=request.user)
        ensure_board(project)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_project(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if not can_access_project(request.user, project):
            return None
        return project

    def get(self, request, project_id):
        project = self.get_project(request, project_id)
        if project is None:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProjectSerializer(project).data)

    def patch(self, request, project_id):
        project = self.get_project(request, project_id)
        if project is None:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        if project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can update this project.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, project_id):
        project = self.get_project(request, project_id)
        if project is None:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        if project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can delete this project.'}, status=status.HTTP_403_FORBIDDEN)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectArchiveView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can archive this project.'}, status=status.HTTP_403_FORBIDDEN)
        project.is_archived = True
        project.save(update_fields=['is_archived'])
        return Response({'message': 'Project archived.'})


class ProjectCloseView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can close this project.'}, status=status.HTTP_403_FORBIDDEN)
        project.is_closed = True
        project.save(update_fields=['is_closed'])
        return Response({'message': 'Project closed.'})


class ProjectMembersView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if not can_access_project(request.user, project):
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        members = [
            {
                'id': project.owner.id,
                'username': project.owner.username,
                'email': project.owner.email,
                'role': 'owner',
            }
        ]
        for role in project.roles.select_related('user').all():
            members.append(
                {
                    'id': role.user.id,
                    'username': role.user.username,
                    'email': role.user.email,
                    'role': role.role_name,
                }
            )
        return Response({'project_id': str(project.id), 'members': members})


class BoardView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if not can_access_project(request.user, project):
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        board = ensure_board(project)
        return Response(
            {
                'project_id': str(project.id),
                'board_id': str(board.id),
                'columns': BoardColumnSerializer(board.columns.all(), many=True).data,
            }
        )


class BoardColumnCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can add columns.'}, status=status.HTTP_403_FORBIDDEN)

        board = ensure_board(project)
        serializer = BoardColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        column = serializer.save(board=board)
        return Response(BoardColumnSerializer(column).data, status=status.HTTP_201_CREATED)


class BoardColumnDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_column(self, column_id):
        return get_object_or_404(BoardColumn, id=column_id)

    def patch(self, request, column_id):
        column = self.get_column(column_id)
        if column.board.project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can update columns.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = BoardColumnSerializer(column, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, column_id):
        column = self.get_column(column_id)
        if column.board.project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can delete columns.'}, status=status.HTTP_403_FORBIDDEN)
        column.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if not can_access_project(request.user, project):
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        roles = project.roles.select_related('user').all()
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can assign roles.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save(project=project)
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_role(self, project_id, role_id):
        return get_object_or_404(Role, id=role_id, project_id=project_id)

    def patch(self, request, project_id, role_id):
        role = self.get_role(project_id, role_id)
        if role.project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can update roles.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, project_id, role_id):
        role = self.get_role(project_id, role_id)
        if role.project.owner_id != request.user.id:
            return Response({'error': 'Only the owner can revoke roles.'}, status=status.HTTP_403_FORBIDDEN)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
