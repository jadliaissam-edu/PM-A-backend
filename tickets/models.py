import uuid

from django.db import models


class Ticket(models.Model): 
    id = models.UUIDField(primary_key=True , default= uuid.uuid4, editable=False ) 
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE, related_name='tickets') 
    title = models.CharField(max_length=255) 
    description = models.TextField(blank=True) 
    type = models.CharField(max_length=50, choices=TicketType.choices) 
    status = models.CharField(max_length=50, default='open', choices=TicketStatus.choices) 
    priority = models.CharField(max_length=50, default='', choices=TicketPriority.choices) 
    estimated_days = models.PositiveIntegerField(default=0) 
    estimated_hours = models.PositiveIntegerField(default=0) 
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta: 
        ordering = ['-created_at'] 
        db_table = 'core_ticket' 




class TicketType(models.TextChoices):
    BUG = "bug", "Bug"
    FEATURE = "feature", "Feature"
    TASK = "task", "Task"

class TicketPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"

class TicketStatus(models.TextChoices):
    TODO = "todo", "To Do"
    IN_PROGRESS = "in_progress", "In Progress"
    DONE = "done", "Done"



class TicketLabel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='labels'
    )

    label = models.CharField(max_length=50)

    class Meta:
        unique_together = ('ticket', 'label')

class TicketAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='ticket_assignments'
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ticket', 'user')



class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='uploaded_attachments'
    )

    file = models.FileField(upload_to='attachments/%Y/%m/%d/')

    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # auto-fill metadata
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size

        super().save(*args, **kwargs)

## 

class TicketLinkType(models.TextChoices):
    BLOCKS = "blocks", "Blocks"
    BLOCKED_BY = "blocked_by", "Blocked By"
    DUPLICATES = "duplicates", "Duplicates"
    RELATED = "related", "Related To"

class TicketLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    source_ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='outgoing_links'
    )

    target_ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='incoming_links'
    )

    link_type = models.CharField(
        max_length=20,
        choices=TicketLinkType.choices
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_ticket', 'target_ticket', 'link_type')