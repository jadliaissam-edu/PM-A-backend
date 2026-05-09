from django.urls import path
from .views import (
    CurrentUserProfileView,
    UserDetailView,
    UserListView,
    DashboardView,
    DashboardStatsView,
    RecentProjectsView,
    DashboardProjectsView,
    ProjectListCreateView,
    ProjectDetailView,
    ProjectArchiveView,
    ProjectCloseView,
    ProjectMembersView,
    ProjectRoleListCreateView,
    ProjectRoleDetailView,
    BoardView,
    BoardColumnCreateView,
    BoardColumnDetailView,
    SprintListCreateView,
    SprintDetailView,
    SprintReportView,
    SprintCompleteView,
    SprintStartView,
    BoardConfigView,
    BoardStatsView,
    BoardTaskSummaryView,
    ProjectProgressReportView,
    SprintProgressReportView,
    MemberProgressReportView,
    ProjectDocumentListView,
    ProjectDocumentDetailView,
    ProjectFileListView,
    ProjectFileDetailView,
    ProjectFromTemplateView,
    OrganizationReleaseListView,
)

urlpatterns = [
    # User endpoints
    path('users/me/', CurrentUserProfileView.as_view(), name='current_user_profile'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('users/', UserListView.as_view(), name='user_list'),
    
    # Dashboard endpoints
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('dashboard/recent-projects/', RecentProjectsView.as_view(), name='recent_projects'),
    path('dashboard/projects/', DashboardProjectsView.as_view(), name='dashboard_projects'),
    
    # Project endpoints
    path('projects/', ProjectListCreateView.as_view(), name='project_list_create'),
    path('projects/<uuid:project_id>/', ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<uuid:project_id>/archive/', ProjectArchiveView.as_view(), name='project_archive'),
    path('projects/<uuid:project_id>/close/', ProjectCloseView.as_view(), name='project_close'),
    path('projects/<uuid:project_id>/members/', ProjectMembersView.as_view(), name='project_members'),
    path('projects/<uuid:project_id>/roles/', ProjectRoleListCreateView.as_view(), name='project_roles'),
    path('projects/<uuid:project_id>/roles/<uuid:role_id>/', ProjectRoleDetailView.as_view(), name='project_role_detail'),
    
    # Board endpoints
    path('projects/<uuid:project_id>/board/', BoardView.as_view(), name='board'),
    path('projects/<uuid:project_id>/board/columns/', BoardColumnCreateView.as_view(), name='board_column_create'),
    path('board/columns/<uuid:column_id>/', BoardColumnDetailView.as_view(), name='board_column_detail'),
    path('projects/<uuid:project_id>/board/config/', BoardConfigView.as_view(), name='board_config'),
    path('projects/<uuid:project_id>/board/stats/', BoardStatsView.as_view(), name='board_stats'),
    path('projects/<uuid:project_id>/board/task-summary/', BoardTaskSummaryView.as_view(), name='board_task_summary'),
    
    # Sprint endpoints
    path('projects/<uuid:project_id>/sprints/', SprintListCreateView.as_view(), name='sprint_list_create'),
    path('projects/<uuid:project_id>/sprints/<uuid:sprint_id>/', SprintDetailView.as_view(), name='sprint_detail'),
    path('projects/<uuid:project_id>/sprints/<uuid:sprint_id>/report/', SprintReportView.as_view(), name='sprint_report'),
    path('projects/<uuid:project_id>/sprints/<uuid:sprint_id>/complete/', SprintCompleteView.as_view(), name='sprint_complete'),
    path('projects/<uuid:project_id>/sprints/<uuid:sprint_id>/start/', SprintStartView.as_view(), name='sprint_start'),
    
    # Progress report endpoints
    path('projects/<uuid:project_id>/progress/', ProjectProgressReportView.as_view(), name='project_progress'),
    path('projects/<uuid:project_id>/sprints/<uuid:sprint_id>/progress/', SprintProgressReportView.as_view(), name='sprint_progress'),
    path('projects/<uuid:project_id>/members/<int:user_id>/progress/', MemberProgressReportView.as_view(), name='member_progress'),
    
    # Document endpoints
    path('projects/<uuid:project_id>/documents/', ProjectDocumentListView.as_view(), name='project_documents'),
    path('projects/<uuid:project_id>/documents/<uuid:document_id>/', ProjectDocumentDetailView.as_view(), name='project_document_detail'),
    
    # File endpoints
    path('projects/<uuid:project_id>/files/', ProjectFileListView.as_view(), name='project_files'),
    path('projects/<uuid:project_id>/files/<uuid:file_id>/', ProjectFileDetailView.as_view(), name='project_file_detail'),
    
    # Release endpoints
    path('releases/', OrganizationReleaseListView.as_view(), name='releases'),
    
    # Template endpoints
    path('projects/from-template/', ProjectFromTemplateView.as_view(), name='project_from_template'),
]
