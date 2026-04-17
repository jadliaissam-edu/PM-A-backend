import uuid

from django.conf import settings
from django.db import models


class Role(models.Model):
	CHEF_DE_PROJECT = 'chef_de_project'
	ADMIN = 'admin'
	DEV = 'dev'
	OBSERVER = 'observer'

	ROLE_CHOICES = [
		(CHEF_DE_PROJECT, 'Chef de projet'),
		(ADMIN, 'Admin'),
		(DEV, 'Dev'),
		(OBSERVER, 'Observer'),
	]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	project = models.ForeignKey('project.Project', on_delete=models.CASCADE, related_name='roles')
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='project_roles',
	)
	role_name = models.CharField(max_length=32, choices=ROLE_CHOICES)
	permissions = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('project', 'user', 'role_name')
		db_table = 'core_role'
