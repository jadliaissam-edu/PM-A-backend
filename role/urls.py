from django.urls import path

from .views import RoleDetailView, RoleListCreateView

urlpatterns = [
    path('projects/<uuid:project_id>/roles/', RoleListCreateView.as_view(), name='project-roles'),
    path('projects/<uuid:project_id>/roles/<uuid:role_id>/', RoleDetailView.as_view(), name='project-role-detail'),
]
