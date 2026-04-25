from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import UserAuditLog

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_logs(request):
    logs = UserAuditLog.objects.all().order_by("-created_at")[:100]
    data = [
        {
            "id": str(log.id),
            "user": log.actor_user.email,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": str(log.target_id),
            "timestamp": log.created_at,
        }
        for log in logs
    ]
    return Response(data)
