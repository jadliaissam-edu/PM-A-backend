from django.contrib import admin
from django.urls import path, include
from rest_framework_spectacular.views import SpectacularAPIView, SpectacularSwaggerAPIView
from project.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check),
    
    # API endpoints
    path('api/', include('accounts.urls')),
    path('api/users/me/', __import__('accounts.views', fromlist=['UserProfileView']).UserProfileView.as_view()),
    path('api/', include('project.urls')),
    path('api/', include('orgs.urls')),
    path('api/', include('tickets.urls')),
    path('api/', include('collaboration.urls')),
    path('api/', include('activity.urls')),
    path('api/', include('role.urls')),
    path('api/', include('search.urls')),
    path('api/', include('core.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerAPIView.as_view(url_name='schema')),
]
