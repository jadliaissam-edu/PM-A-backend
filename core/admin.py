from django.contrib import admin

from .models import BoardColumn, Project, ProjectBoard, Role


admin.site.register(Project)
admin.site.register(ProjectBoard)
admin.site.register(BoardColumn)
admin.site.register(Role)
