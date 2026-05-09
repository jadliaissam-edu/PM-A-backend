from django.urls import path
from .views import (
    RegisterView,
    EmailTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetVerifyOTPView,
    PasswordResetConfirmView,
    MFASetupView,
    MFAVerifyView,
    OAuthLoginView,
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', EmailTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Password Reset Flow
    path('auth/reset-password/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/reset-password/verify-otp/', PasswordResetVerifyOTPView.as_view(), name='password_reset_verify_otp'),
    path('auth/reset-password/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # MFA endpoints
    path('auth/mfa/setup/', MFASetupView.as_view(), name='mfa_setup'),
    path('auth/mfa/verify/', MFAVerifyView.as_view(), name='mfa_verify'),
    
    # OAuth endpoints
    path('auth/oauth/login/', OAuthLoginView.as_view(), name='oauth_login'),
    
    # Legacy endpoints for backward compatibility
    path('login/', EmailTokenObtainPairView.as_view(), name='legacy_login'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='legacy_token_refresh'),
]
