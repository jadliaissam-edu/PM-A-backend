import uuid

from django.conf import settings
from django.db import models


class Project(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True, default='')
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='owned_projects',
	)
	is_archived = models.BooleanField(default=False)
	is_closed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		db_table = 'core_project'


class ProjectBoard(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='board')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'core_projectboard'


class BoardColumn(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='columns')
	name = models.CharField(max_length=120)
	position = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['position', 'name']
		db_table = 'core_boardcolumn'
		
class SprintStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"


class Sprint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    board = models.ForeignKey(
        'project.ProjectBoard',
        on_delete=models.CASCADE,
        related_name='sprints'
    )

    name = models.CharField(max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=SprintStatus.choices,
        default=SprintStatus.PLANNED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_sprint"
        ordering = ["-start_date"]
		
class BoardFilter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey("project.ProjectBoard", on_delete=models.CASCADE)

    assignees = models.ManyToManyField("accounts.User", blank=True)
    labels = models.ManyToManyField("tickets.TicketLabel", blank=True)

    priorities = models.JSONField(default=list, blank=True)
