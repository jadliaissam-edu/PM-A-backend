
import uuid
from django.db import models
from django.conf import settings

class ProjectType(models.TextChoices):
    SOFTWARE = "software", "Software"
    BUSINESS = "business", "Business"
    SUPPORT = "support", "Support"

class ProjectVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    INTERNAL = "internal", "Internal"
    PUBLIC = "public", "Public"

class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    CLOSED = "closed", "Closed"

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey('orgs.Workspace', on_delete=models.CASCADE, related_name='projects', null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=50, choices=ProjectType.choices, default=ProjectType.SOFTWARE)
    visibility = models.CharField(max_length=50, choices=ProjectVisibility.choices, default=ProjectVisibility.PRIVATE)
    status = models.CharField(max_length=50, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

# =========================
# Sprint
# =========================
class Sprint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey('ProjectBoard', on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50)

# =========================
# Project Membership & Roles
# =========================
class RoleName(models.TextChoices):
    ADMIN = "admin", "Admin"
    CHEF_DE_PROJET = "chef_de_projet", "ChefDeProjet"
    DEVELOPPEUR = "developpeur", "Developpeur"
    OBSERVATEUR = "observateur", "Observateur"

class ProjectMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=50, choices=RoleName.choices, default=RoleName.OBSERVATEUR)

class ProjectFavorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='favorited_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_projects')
    created_at = models.DateTimeField(auto_now_add=True)

class RecentProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recent_projects')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='recently_accessed_by')
    last_access_at = models.DateTimeField(auto_now=True)

# =========================
# Project Dashboard & Widgets
# =========================
class ProjectDashboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='dashboard')

class WidgetType(models.TextChoices):
    BURNDOWN = "burndown", "Burndown"
    VELOCITY = "velocity", "Velocity"
    CFD = "cfd", "CFD"
    OPEN_ISSUES = "open_issues", "OpenIssues"
    RECENT_ACTIVITY = "recent_activity", "RecentActivity"

class DashboardWidget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(ProjectDashboard, on_delete=models.CASCADE, related_name='widgets')
    type = models.CharField(max_length=50, choices=WidgetType.choices)
    position = models.IntegerField(default=0)
    config_json = models.JSONField(default=dict)

# =========================
# Board & Columns
# =========================
class BoardType(models.TextChoices):
    KANBAN = "kanban", "Kanban"
    SCRUM = "scrum", "Scrum"

class BoardViewMode(models.TextChoices):
    LIST = "list", "List"
    BOARD = "board", "Board"
    TIMELINE = "timeline", "Timeline"

class ProjectBoard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='board')
    board_type = models.CharField(max_length=50, choices=BoardType.choices, default=BoardType.KANBAN)
    view_mode = models.CharField(max_length=50, choices=BoardViewMode.choices, default=BoardViewMode.BOARD)

class BoardColumn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    position = models.IntegerField(default=0)
    wip_limit = models.IntegerField(default=0)
    is_done_column = models.BooleanField(default=False)

class TicketPriority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"

class BoardFilter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='filters')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    priority = models.CharField(max_length=50, choices=TicketPriority.choices, blank=True)
    labels = models.JSONField(default=list, blank=True)

class SwimlaneType(models.TextChoices):
    EPIC = "epic", "Epic"
    ASSIGNEE = "assignee", "Assignee"

class Swimlane(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='swimlanes')
    type = models.CharField(max_length=50, choices=SwimlaneType.choices)
    value = models.CharField(max_length=255)

# =========================
# Sprint & Reports
# =========================
class SprintStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"

class Sprint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, choices=SprintStatus.choices, default=SprintStatus.PLANNED)

class SprintReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name='report')
    total_tickets = models.IntegerField(default=0)
    done_tickets = models.IntegerField(default=0)
    remaining_tickets = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)
    generated_at = models.DateTimeField(auto_now_add=True)

class VelocityChart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name='velocity_chart')
    data_json = models.JSONField(default=dict)

class BurndownChart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name='burndown_chart')
    data_json = models.JSONField(default=dict)

class RetrospectiveBoard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name='retrospective_board')
    format = models.CharField(max_length=255)

# =========================
# Release & Notes
# =========================
class ReleaseStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    IN_PROGRESS = "in_progress", "InProgress"
    RELEASED = "released", "Released"
    ARCHIVED = "archived", "Archived"

class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='releases')
    tag = models.CharField(max_length=255)
    target_date = models.DateField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=ReleaseStatus.choices, default=ReleaseStatus.PLANNED)

class ReleaseDashboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    release = models.OneToOneField(Release, on_delete=models.CASCADE, related_name='dashboard')
    progress_percent = models.FloatField(default=0.0)
    resolved_issues = models.IntegerField(default=0)
    remaining_issues = models.IntegerField(default=0)

class ReleaseHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='release_histories')
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    archived_at = models.DateTimeField()

class ReleaseNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    release = models.OneToOneField(Release, on_delete=models.CASCADE, related_name='release_note')
    content_markdown = models.TextField(blank=True)
    generated_by_ai = models.BooleanField(default=False)

# =========================
# Report Scope
# =========================
class ReportScope(models.TextChoices):
    PROJECT = "project", "Project"
    SPRINT = "sprint", "Sprint"
    MEMBER = "member", "Member"

class ProgressReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(max_length=50, choices=ReportScope.choices)
    scope_id = models.UUIDField()
    generated_at = models.DateTimeField(auto_now_add=True)
    completion_rate = models.FloatField(default=0.0)
    velocity = models.FloatField(default=0.0)
    open_issues = models.IntegerField(default=0)

class ExportFormat(models.TextChoices):
    PDF = "pdf", "PDF"
    CSV = "csv", "CSV"

class ReportExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ProgressReport, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=50, choices=ExportFormat.choices)
    file_url = models.URLField()

class CumulativeFlowDiagram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cfds')
    data_json = models.JSONField(default=dict)



# SPRINT_REPORT model
from django.utils import timezone

class SprintReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.ForeignKey('Sprint', on_delete=models.CASCADE, related_name='reports')
    total_tickets = models.IntegerField()
    done_tickets = models.IntegerField()
    remaining_tickets = models.IntegerField()
    completion_rate = models.FloatField()
    generated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Report for {self.sprint.name} at {self.generated_at}"


     

