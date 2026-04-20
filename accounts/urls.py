from django.urls import path 
from  rest_framework_simplejwt.views import ( 
    TokenRefreshView, 
) 
from .views import  EmailTokenObtainPairView, PasswordResetRequestView
from .views import  PasswordResetConfirmView 
from .views import PasswordResetVerifyOTPView
from .views import MFASetupView, MFAVerifyView
from .views import  RegisterView, LogoutView
urlpatterns = [ 
    path('login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('register/', RegisterView.as_view(), name='register'),
    path('mfa/setup/', MFASetupView.as_view(), name='mfa-setup'),
    path('mfa/verify/', MFAVerifyView.as_view(), name='mfa-verify'),
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset-password-request'),
    path('reset-password/verify-otp/', PasswordResetVerifyOTPView.as_view(), name='reset-password-verify-otp'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='reset-password-confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
]