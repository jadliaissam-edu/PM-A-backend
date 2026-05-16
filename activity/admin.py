from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = ('id', 'actor', 'action', 'project_id', 'created_at')
	list_filter = ('action', 'created_at')
	search_fields = ('actor__username', 'description')
	readonly_fields = ('id', 'created_at')

