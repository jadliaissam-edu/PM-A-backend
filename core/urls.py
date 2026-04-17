from django.urls import path

from .views import (
    BoardColumnCreateView,
    BoardColumnDetailView,
    BoardView,
    CurrentUserProfileView,
    DashboardStatsView,
    DashboardView,
    ProjectArchiveView,
    ProjectCloseView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectMembersView,
    RecentProjectsView,
    RoleDetailView,
    RoleListCreateView,
    UserDetailView,
    health_check,
)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('users/me/', CurrentUserProfileView.as_view(), name='current-user-profile'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/recent-projects/', RecentProjectsView.as_view(), name='dashboard-recent-projects'),
    path('projects/', ProjectListCreateView.as_view(), name='project-list-create'),
    path('projects/<uuid:project_id>/', ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<uuid:project_id>/archive/', ProjectArchiveView.as_view(), name='project-archive'),
    path('projects/<uuid:project_id>/close/', ProjectCloseView.as_view(), name='project-close'),
    path('projects/<uuid:project_id>/members/', ProjectMembersView.as_view(), name='project-members'),
    path('projects/<uuid:project_id>/board/', BoardView.as_view(), name='project-board'),
    path('projects/<uuid:project_id>/board/columns/', BoardColumnCreateView.as_view(), name='board-column-create'),
    path('board/columns/<uuid:column_id>/', BoardColumnDetailView.as_view(), name='board-column-detail'),
    path('projects/<uuid:project_id>/roles/', RoleListCreateView.as_view(), name='project-roles'),
    path('projects/<uuid:project_id>/roles/<uuid:role_id>/', RoleDetailView.as_view(), name='project-role-detail'),
]