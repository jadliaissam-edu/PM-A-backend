from django.contrib.contenttypes.models import ContentType
from .models import ActivityLog

def log_activity(actor, target, action, description="", project_id=None, old_value=None, new_value=None):
    """
    Utility to log an activity.
    target: The object being acted upon (Ticket, File, etc.)
    """
    content_type = ContentType.objects.get_for_model(target)
    return ActivityLog.objects.create(
        actor=actor,
        content_type=content_type,
        object_id=target.id,
        project_id=project_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value
    )
