from django.contrib import admin

from .models import Dashboard, MFAConfig, Project, ProjectBoard, Role, RolePermission


admin.site.register(MFAConfig)
admin.site.register(Dashboard)
admin.site.register(Project)
admin.site.register(ProjectBoard)
admin.site.register(Role)
admin.site.register(RolePermission)
