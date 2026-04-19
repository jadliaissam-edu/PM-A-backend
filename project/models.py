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
	pricing_plan_id = models.UUIDField(null=True, blank=True)
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
	wip_limit = models.IntegerField(default=0)
	is_done_column = models.BooleanField(default=False)

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
    goal = models.TextField(blank=True, default='')

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

class Dashboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards')

    class Meta:
        db_table = "core_dashboard"

class SprintReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name='auto_report')
    total_tickets = models.IntegerField(default=0)
    done_tickets = models.IntegerField(default=0)
    remaining_tickets = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_sprint_report"

class BacklogItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='backlog')
    ticket = models.OneToOneField('tickets.Ticket', on_delete=models.CASCADE, related_name='backlog_item')
    rank = models.IntegerField(default=0)
    priority_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_backlog_item"
        ordering = ["rank"]

class ReleaseStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    RELEASED = "released", "Released"

class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='releases')
    tag = models.CharField(max_length=100)
    target_date = models.DateField()
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=ReleaseStatus.choices, default=ReleaseStatus.PLANNED)

    class Meta:
        db_table = "core_release"
        ordering = ["-target_date"]

class ReleaseDashboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    release = models.OneToOneField(Release, on_delete=models.CASCADE, related_name='dashboard')
    progress_percent = models.FloatField(default=0.0)
    resolved_issues = models.IntegerField(default=0)
    remaining_issues = models.IntegerField(default=0)

    class Meta:
        db_table = "core_release_dashboard"

class ProgressReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(max_length=50) # 'project', 'sprint', 'user'
    scope_id = models.UUIDField()
    completion_rate = models.FloatField(default=0.0)
    velocity = models.FloatField(default=0.0)
    open_issues = models.IntegerField(default=0)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_progress_report"
        ordering = ["-generated_at"]
