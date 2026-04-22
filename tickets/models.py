
import uuid
from django.db import models
from django.conf import settings
from project.models import Project

# =========================
# Ticket Types, Priority, Status
# =========================
class TicketType(models.TextChoices):
    BUG = "bug", "Bug"
    FEATURE = "feature", "Feature"
    TASK = "task", "Task"
    EPIC = "epic", "Epic"
    STORY = "story", "Story"
    SUBTASK = "sub_task", "SubTask"

class TicketPriority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"

class TicketStatus(models.TextChoices):
    TODO = "todo", "ToDo"
    IN_PROGRESS = "in_progress", "InProgress"
    IN_REVIEW = "in_review", "InReview"
    DONE = "done", "Done"

# =========================
# Ticket Core Model
# =========================
class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, related_name='tickets')
    current_column = models.ForeignKey('project.BoardColumn', null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets')
    sprint = models.ForeignKey('project.Sprint', null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets')
    release = models.ForeignKey('project.Release', null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets')
    title = models.CharField(max_length=255)
    description_markdown = models.TextField(blank=True)
    type = models.CharField(max_length=50, choices=TicketType.choices, default=TicketType.TASK)
    priority = models.CharField(max_length=50, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)
    status = models.CharField(max_length=50, choices=TicketStatus.choices, default=TicketStatus.TODO)
    labels = models.JSONField(default=list, blank=True)
    estimate_story_points = models.FloatField(default=0.0)
    estimate_hours = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

# =========================
# Assignment & Time Tracking
# =========================
class TicketAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ticket_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

class TimeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_entries')
    hours_spent = models.FloatField()
    comment = models.TextField(blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()

# =========================
# Attachments
# =========================
class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_attachments')
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=500, blank=True, null=True)
    mime_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

# =========================
# Ticket Links
# =========================
class TicketLinkType(models.TextChoices):
    BLOCKS = "blocks", "Blocks"
    BLOCKED_BY = "blocked_by", "BlockedBy"
    DUPLICATES = "duplicates", "Duplicates"
    RELATED_TO = "related_to", "RelatedTo"

class TicketLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='outgoing_links')
    target_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='incoming_links')
    link_type = models.CharField(max_length=50, choices=TicketLinkType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

# =========================
# Audit Log
# =========================
class TicketAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='audit_logs')
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

# =========================
# Search & Import
# =========================
class TicketSearchQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=255, blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=50, choices=TicketPriority.choices, blank=True)
    labels = models.JSONField(default=list, blank=True)
    from_date = models.DateTimeField(null=True, blank=True)
    to_date = models.DateTimeField(null=True, blank=True)

class ImportFormat(models.TextChoices):
    CSV = "csv", "CSV"
    MARKDOWN = "markdown", "Markdown"

class ImportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"

class TicketImportJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    format = models.CharField(max_length=50, choices=ImportFormat.choices)
    source_file_url = models.CharField(max_length=500)
    status = models.CharField(max_length=50, choices=ImportStatus.choices, default=ImportStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

class TicketMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='movements')
    from_column = models.ForeignKey('project.BoardColumn', on_delete=models.SET_NULL, null=True, related_name='moved_from')
    to_column = models.ForeignKey('project.BoardColumn', on_delete=models.SET_NULL, null=True, related_name='moved_to')
    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    moved_at = models.DateTimeField(auto_now_add=True)

class BacklogItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='backlog_items')
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='backlog_items')
    rank = models.IntegerField()
    priority_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)