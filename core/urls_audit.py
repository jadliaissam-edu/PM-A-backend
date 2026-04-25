from django.urls import path
from .views_audit import audit_logs

urlpatterns = [
    path('audit/logs/', audit_logs),
]
