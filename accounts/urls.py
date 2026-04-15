from django.urls import path 
from  rest_framework_simplejwt.views import ( 
    TokenObtainPairView,
    TokenRefreshView, 
) 
from .views import  PasswordResetRequestView
from .views import  PasswordResetConfirmView 
from .views import  RegisterView 
urlpatterns = [ 
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path('register/', RegisterView.as_view(), name='register'),
    path("reset-password/", PasswordResetRequestView.as_view()),
    path("reset-password-confirm/", PasswordResetConfirmView.as_view())
]