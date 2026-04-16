from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ─────────────────────────────────────────────
#  ENUMERATIONS
# ─────────────────────────────────────────────

class OAuthProvider(models.TextChoices):
    GITHUB = "GitHub", "GitHub"
    GOOGLE = "Google", "Google"


class TicketType(models.TextChoices):
    BUG = "Bug", "Bug"
    FEATURE = "Feature", "Feature"
    TASK = "Task", "Task"
    EPIC = "Epic", "Epic"
    STORY = "Story", "Story"
    SUBTASK = "SubTask", "Sub-Task"


class TicketPriority(models.TextChoices):
    CRITICAL = "Critical", "Critical"
    HIGH = "High", "High"
    MEDIUM = "Medium", "Medium"
    LOW = "Low", "Low"


class TicketStatus(models.TextChoices):
    TODO = "ToDo", "To Do"
    IN_PROGRESS = "InProgress", "In Progress"
    IN_REVIEW = "InReview", "In Review"
    DONE = "Done", "Done"


class RoleName(models.TextChoices):
    ADMIN = "Admin", "Admin"
    CHEF_DE_PROJET = "ChefDeProjet", "Chef de Projet"
    DEVELOPPEUR = "Developpeur", "Développeur"
    OBSERVATEUR = "Observateur", "Observateur"


class BoardType(models.TextChoices):
    KANBAN = "Kanban", "Kanban"
    SCRUM = "Scrum", "Scrum"


class BoardViewMode(models.TextChoices):
    LIST = "List", "List"
    BOARD = "Board", "Board"
    TIMELINE = "Timeline", "Timeline"


class SwimlaneType(models.TextChoices):
    EPIC = "Epic", "Epic"
    ASSIGNEE = "Assignee", "Assignee"


class SprintStatus(models.TextChoices):
    PLANNED = "Planned", "Planned"
    ACTIVE = "Active", "Active"
    CLOSED = "Closed", "Closed"


class ProjectType(models.TextChoices):
    SOFTWARE = "Software", "Software"
    BUSINESS = "Business", "Business"
    SUPPORT = "Support", "Support"


class ProjectVisibility(models.TextChoices):
    PRIVATE = "Private", "Private"
    INTERNAL = "Internal", "Internal"
    PUBLIC = "Public", "Public"


class ProjectStatus(models.TextChoices):
    ACTIVE = "Active", "Active"
    ARCHIVED = "Archived", "Archived"
    CLOSED = "Closed", "Closed"


class ReleaseStatus(models.TextChoices):
    PLANNED = "Planned", "Planned"
    IN_PROGRESS = "InProgress", "In Progress"
    RELEASED = "Released", "Released"
    ARCHIVED = "Archived", "Archived"


class TicketLinkType(models.TextChoices):
    BLOCKS = "Blocks", "Blocks"
    BLOCKED_BY = "BlockedBy", "Blocked By"
    DUPLICATES = "Duplicates", "Duplicates"
    RELATED_TO = "RelatedTo", "Related To"


class ReactionType(models.TextChoices):
    LIKE = "Like", "Like"
    LOVE = "Love", "Love"
    LAUGH = "Laugh", "Laugh"
    EYES = "Eyes", "Eyes"
    ROCKET = "Rocket", "Rocket"


class ReportScope(models.TextChoices):
    PROJECT = "Project", "Project"
    SPRINT = "Sprint", "Sprint"
    MEMBER = "Member", "Member"


class WidgetType(models.TextChoices):
    BURNDOWN = "Burndown", "Burndown"
    VELOCITY = "Velocity", "Velocity"
    CFD = "CFD", "Cumulative Flow Diagram"
    OPEN_ISSUES = "OpenIssues", "Open Issues"
    RECENT_ACTIVITY = "RecentActivity", "Recent Activity"


class ImportFormat(models.TextChoices):
    CSV = "CSV", "CSV"
    MARKDOWN = "Markdown", "Markdown"


class ImportStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    RUNNING = "Running", "Running"
    SUCCESS = "Success", "Success"
    FAILED = "Failed", "Failed"


class ExportFormat(models.TextChoices):
    PDF = "PDF", "PDF"
    CSV = "CSV", "CSV"


class NotificationChannel(models.TextChoices):
    WEBSOCKET = "WebSocket", "WebSocket"


# ─────────────────────────────────────────────
#  USER & AUTH
# ─────────────────────────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    preferences_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"Profile({self.user.email})"


class MFAConfig(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mfa_config")
    secret = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=50)

    class Meta:
        db_table = "mfa_configs"

    def __str__(self):
        return f"MFA({self.user.email})"


class OAuthAccount(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="oauth_accounts")
    provider = models.CharField(max_length=20, choices=OAuthProvider.choices)
    provider_user_id = models.CharField(max_length=255)

    class Meta:
        db_table = "oauth_accounts"
        unique_together = ("provider", "provider_user_id")

    def __str__(self):
        return f"{self.provider}:{self.provider_user_id}"


class UserAuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor} → {self.action}"


# ─────────────────────────────────────────────
#  ORGANIZATION & WORKSPACE
# ─────────────────────────────────────────────

class Organization(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "organizations"

    def __str__(self):
        return self.name


class Workspace(models.Model):
    id = models.AutoField(primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="workspaces")
    name = models.CharField(max_length=255)
    visibility = models.CharField(max_length=20, choices=ProjectVisibility.choices, default=ProjectVisibility.PRIVATE)

    class Meta:
        db_table = "workspaces"

    def __str__(self):
        return f"{self.organization.name}/{self.name}"


class Invitation(models.Model):
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="invitations")
    invited_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="invitations")
    email = models.EmailField()
    invite_link = models.URLField()
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "invitations"

    def __str__(self):
        return f"Invite({self.email} → {self.workspace.name})"


# ─────────────────────────────────────────────
#  PROJECT
# ─────────────────────────────────────────────

class Project(models.Model):
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=ProjectType.choices, default=ProjectType.SOFTWARE)
    visibility = models.CharField(max_length=20, choices=ProjectVisibility.choices, default=ProjectVisibility.PRIVATE)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "projects"

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(max_length=30, choices=RoleName.choices, default=RoleName.DEVELOPPEUR)

    class Meta:
        db_table = "project_members"
        unique_together = ("project", "user")

    def __str__(self):
        return f"{self.user.email} → {self.project.name} [{self.role}]"


class ProjectFavorite(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="favorites")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_projects")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "project_favorites"
        unique_together = ("project", "user")

    def __str__(self):
        return f"{self.user.email} ♥ {self.project.name}"


class RecentProject(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recent_projects")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="recent_accesses")
    last_access_at = models.DateTimeField(default=timezone.now)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        db_table = "recent_projects"
        unique_together = ("user", "project")
        ordering = ["-last_access_at"]

    def __str__(self):
        return f"{self.user.email} accessed {self.project.name}"


# ─────────────────────────────────────────────
#  PROJECT DASHBOARD
# ─────────────────────────────────────────────

class ProjectDashboard(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="dashboard")

    class Meta:
        db_table = "project_dashboards"

    def __str__(self):
        return f"Dashboard({self.project.name})"


class DashboardWidget(models.Model):
    id = models.AutoField(primary_key=True)
    dashboard = models.ForeignKey(ProjectDashboard, on_delete=models.CASCADE, related_name="widgets")
    type = models.CharField(max_length=30, choices=WidgetType.choices)
    position = models.PositiveIntegerField(default=0)
    config_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "dashboard_widgets"
        ordering = ["position"]

    def __str__(self):
        return f"{self.type} @ pos {self.position}"


# ─────────────────────────────────────────────
#  BOARD & COLUMNS
# ─────────────────────────────────────────────

class ProjectBoard(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="board")
    board_type = models.CharField(max_length=20, choices=BoardType.choices, default=BoardType.KANBAN)
    view_mode = models.CharField(max_length=20, choices=BoardViewMode.choices, default=BoardViewMode.BOARD)

    class Meta:
        db_table = "project_boards"

    def __str__(self):
        return f"Board({self.project.name})"


class BoardColumn(models.Model):
    id = models.AutoField(primary_key=True)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)
    wip_limit = models.PositiveIntegerField(null=True, blank=True)
    is_done_column = models.BooleanField(default=False)

    class Meta:
        db_table = "board_columns"
        ordering = ["position"]

    def __str__(self):
        return f"{self.board.project.name} / {self.name}"


class BoardFilter(models.Model):
    id = models.AutoField(primary_key=True)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name="filters")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=TicketPriority.choices, null=True, blank=True)
    labels = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "board_filters"

    def __str__(self):
        return f"Filter({self.board})"


class Swimlane(models.Model):
    id = models.AutoField(primary_key=True)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name="swimlanes")
    type = models.CharField(max_length=20, choices=SwimlaneType.choices)
    value = models.CharField(max_length=255)

    class Meta:
        db_table = "swimlanes"

    def __str__(self):
        return f"{self.type}: {self.value}"


# ─────────────────────────────────────────────
#  SPRINT
# ─────────────────────────────────────────────

class Sprint(models.Model):
    id = models.AutoField(primary_key=True)
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name="sprints")
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SprintStatus.choices, default=SprintStatus.PLANNED)

    class Meta:
        db_table = "sprints"

    def __str__(self):
        return f"{self.name} [{self.status}]"


class SprintReport(models.Model):
    id = models.AutoField(primary_key=True)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="report")
    total_tickets = models.PositiveIntegerField(default=0)
    done_tickets = models.PositiveIntegerField(default=0)
    remaining_tickets = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "sprint_reports"

    def __str__(self):
        return f"Report({self.sprint.name})"


class VelocityChart(models.Model):
    id = models.AutoField(primary_key=True)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="velocity_chart")
    data_json = models.JSONField(default=dict)

    class Meta:
        db_table = "velocity_charts"

    def __str__(self):
        return f"Velocity({self.sprint.name})"


class BurndownChart(models.Model):
    id = models.AutoField(primary_key=True)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="burndown_chart")
    data_json = models.JSONField(default=dict)

    class Meta:
        db_table = "burndown_charts"

    def __str__(self):
        return f"Burndown({self.sprint.name})"


class RetrospectiveBoard(models.Model):
    id = models.AutoField(primary_key=True)
    sprint = models.OneToOneField(Sprint, on_delete=models.CASCADE, related_name="retrospective")
    format = models.CharField(max_length=100, default="Start/Stop/Continue")
    is_open = models.BooleanField(default=False)

    class Meta:
        db_table = "retrospective_boards"

    def __str__(self):
        return f"Retro({self.sprint.name})"


# ─────────────────────────────────────────────
#  TICKETS
# ─────────────────────────────────────────────

class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tickets")
    current_column = models.ForeignKey(
        BoardColumn, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets"
    )
    sprint = models.ForeignKey(
        Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets"
    )
    release = models.ForeignKey(
        "Release", on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets"
    )
    title = models.CharField(max_length=500)
    description_markdown = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TicketType.choices, default=TicketType.TASK)
    priority = models.CharField(max_length=20, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.TODO)
    labels = models.JSONField(default=list, blank=True)
    estimate_story_points = models.FloatField(null=True, blank=True)
    estimate_hours = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.type}] {self.title}"


class TicketAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_assignments")
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ticket_assignments"
        unique_together = ("ticket", "user")

    def __str__(self):
        return f"{self.user.email} → {self.ticket.title}"


class TicketLink(models.Model):
    id = models.AutoField(primary_key=True)
    source_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="outgoing_links")
    target_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="incoming_links")
    link_type = models.CharField(max_length=20, choices=TicketLinkType.choices)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ticket_links"

    def __str__(self):
        return f"{self.source_ticket.title} --{self.link_type}--> {self.target_ticket.title}"


class TicketMovement(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="movements")
    from_column = models.ForeignKey(BoardColumn, on_delete=models.SET_NULL, null=True, related_name="movements_from")
    to_column = models.ForeignKey(BoardColumn, on_delete=models.SET_NULL, null=True, related_name="movements_to")
    moved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="ticket_movements")
    moved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ticket_movements"
        ordering = ["-moved_at"]

    def __str__(self):
        return f"{self.ticket.title}: {self.from_column} → {self.to_column}"


class TicketAuditLog(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="ticket_audit_logs")
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ticket_audit_logs"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.ticket.title}.{self.field_name} changed by {self.actor}"


class TicketImportJob(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="import_jobs")
    format = models.CharField(max_length=20, choices=ImportFormat.choices)
    source_file_url = models.URLField()
    status = models.CharField(max_length=20, choices=ImportStatus.choices, default=ImportStatus.PENDING)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ticket_import_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Import({self.project.name}, {self.format}) [{self.status}]"


# ─────────────────────────────────────────────
#  TIME ENTRIES & ATTACHMENTS
# ─────────────────────────────────────────────

class TimeEntry(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="time_entries")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="time_entries")
    hours_spent = models.FloatField()
    comment = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "time_entries"

    def __str__(self):
        return f"{self.user.email}: {self.hours_spent}h on {self.ticket.title}"


class Attachment(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploads")
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size in bytes")
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "attachments"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.file_name


# ─────────────────────────────────────────────
#  COMMENTS & REACTIONS
# ─────────────────────────────────────────────

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    mentions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on {self.ticket.title}"


class Reaction(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    type = models.CharField(max_length=20, choices=ReactionType.choices)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "reactions"
        unique_together = ("comment", "user", "type")

    def __str__(self):
        return f"{self.user.email} reacted {self.type}"


# ─────────────────────────────────────────────
#  RELEASES
# ─────────────────────────────────────────────

class Release(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="releases")
    tag = models.CharField(max_length=100)
    target_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ReleaseStatus.choices, default=ReleaseStatus.PLANNED)

    class Meta:
        db_table = "releases"

    def __str__(self):
        return f"{self.project.name} v{self.tag}"


class ReleaseDashboard(models.Model):
    id = models.AutoField(primary_key=True)
    release = models.OneToOneField(Release, on_delete=models.CASCADE, related_name="dashboard")
    progress_percent = models.FloatField(default=0.0)
    resolved_issues = models.PositiveIntegerField(default=0)
    remaining_issues = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "release_dashboards"

    def __str__(self):
        return f"ReleaseDashboard({self.release})"


class ReleaseNote(models.Model):
    id = models.AutoField(primary_key=True)
    release = models.OneToOneField(Release, on_delete=models.CASCADE, related_name="note")
    content_markdown = models.TextField()
    generated_by_ai = models.BooleanField(default=False)

    class Meta:
        db_table = "release_notes"

    def __str__(self):
        return f"ReleaseNote({self.release})"


class ReleaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="release_history")
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name="history_entries")
    archived_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "release_history"
        ordering = ["-archived_at"]

    def __str__(self):
        return f"History({self.release})"


# ─────────────────────────────────────────────
#  REPORTS
# ─────────────────────────────────────────────

class ProgressReport(models.Model):
    id = models.AutoField(primary_key=True)
    scope = models.CharField(max_length=20, choices=ReportScope.choices)
    scope_id = models.IntegerField()
    generated_at = models.DateTimeField(default=timezone.now)
    completion_rate = models.FloatField(default=0.0)
    velocity = models.FloatField(default=0.0)
    open_issues = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "progress_reports"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"ProgressReport({self.scope}:{self.scope_id})"


class ReportExport(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey(ProgressReport, on_delete=models.CASCADE, related_name="exports")
    format = models.CharField(max_length=10, choices=ExportFormat.choices)
    file_url = models.URLField()

    class Meta:
        db_table = "report_exports"

    def __str__(self):
        return f"Export({self.report} as {self.format})"


class CumulativeFlowDiagram(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="cfd_charts")
    data_json = models.JSONField(default=dict)

    class Meta:
        db_table = "cumulative_flow_diagrams"

    def __str__(self):
        return f"CFD({self.project.name})"


# ─────────────────────────────────────────────
#  NOTIFICATIONS
# ─────────────────────────────────────────────

class NotificationEvent(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notifications")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    event_type = models.CharField(max_length=100)
    payload_json = models.JSONField(default=dict)
    channel = models.CharField(
        max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.WEBSOCKET
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notification_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification({self.event_type} → {self.user.email})"
