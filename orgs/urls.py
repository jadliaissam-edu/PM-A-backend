from django.urls import path
from .views import (
    OrganizationListView,
    OrganizationDetailView,
    WorkspaceListCreateView,
    WorkspaceDetailView,
    OrganizationTreeView,
)

urlpatterns = [
    # Organization endpoints
    path('orgs/', OrganizationListView.as_view(), name='organization_list'),
    path('orgs/<uuid:org_id>/', OrganizationDetailView.as_view(), name='organization_detail'),
    path('orgs/tree/', OrganizationTreeView.as_view(), name='orgs_tree'),
    
    # Workspace endpoints
    path('workspaces/', WorkspaceListCreateView.as_view(), name='workspace_list_create'),
    path('workspaces/<uuid:workspace_id>/', WorkspaceDetailView.as_view(), name='workspace_detail'),
]
