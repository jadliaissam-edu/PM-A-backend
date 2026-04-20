"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include 
from rest_framework_simplejwt.views import ( 
    TokenObtainPairView,
    TokenRefreshView, 
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import TokenVerifyView
from django.conf.urls.static import static 
from config import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair_legacy'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_legacy'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify_legacy'),
    path('api/',include('project.urls')),
    path('api/',include('role.urls')),
    path('api/auth/',include('accounts.urls')), 
    path('api/orgs/', include('orgs.urls')),
    path('api/core/', include('core.urls')),
    
    # OpenAPI schema (JSON)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Redoc (alternative UI)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    
]
# For serving media files during development  (only in dev mode)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)