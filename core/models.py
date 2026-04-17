import uuid

from django.conf import settings
from django.db import models


class MFAConfig(models.Model):
	class Method(models.TextChoices):
		SMS = "sms", "SMS"
		EMAIL = "email", "Email"
		AUTHENTICATOR = "authenticator", "Authenticator App"

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="core_mfa_config",
	)
	secret = models.CharField(max_length=255)
	is_enabled = models.BooleanField(default=False)
	method = models.CharField(max_length=20, choices=Method.choices)

	class Meta:
		db_table = "mfa_configs"

	

class Dashboard(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="dashboards",
	)

	class Meta:
		db_table = "dashboards"



class Project(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="owned_projects",
	)
	dashboard = models.ForeignKey(
		Dashboard,
		on_delete=models.CASCADE,
		related_name="projects",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "projects"

class ProjectBoard(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	project = models.OneToOneField(
		Project,
		on_delete=models.CASCADE,
		related_name="board",
	)

	class Meta:
		db_table = "project_boards"

class Role(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	project = models.ForeignKey(
		Project,
		on_delete=models.CASCADE,
		related_name="roles",
	)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="project_roles",
	)
	role_name = models.CharField(max_length=100)

	class Meta:
		db_table = "roles"
		constraints = [
			models.UniqueConstraint(fields=["project", "user"], name="unique_project_user_role")
		]

class RolePermission(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	role = models.ForeignKey(
		Role,
		on_delete=models.CASCADE,
		related_name="permissions",
	)
	permission = models.CharField(max_length=100)

	class Meta:
		db_table = "role_permissions"
		constraints = [
			models.UniqueConstraint(fields=["role", "permission"], name="unique_role_permission")
		]


