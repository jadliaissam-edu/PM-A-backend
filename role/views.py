from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.authentication import JWTAuthentication

from project.models import Project

from .models import Role
from .serializer import RoleSerializer


def can_access_project(user, project):
	return project.owner_id == user.id or project.roles.filter(user=user).exists()


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
