

# Standard library imports
import random
import requests
from datetime import timedelta

# Django imports
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

# Third-party imports
from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

# Local imports
from accounts.models import MFAConfig, PasswordResetOTP, OAuthAccount, OAuthProvider
from .services.mfa_service import generate_mfa_secret, generate_qr_url, verify_mfa_token
from .serializer import (
    EmailTokenObtainPairSerializer,
    MFASetupSerializer,
    MFAVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifyOTPSerializer,
    RegisterSerializer,
    OAuthLoginSerializer,
)
from django.contrib.contenttypes.models import ContentType
from activity.models import ActivityLog

from .serializer import ProfileSerializer
from .models import UserProfile


# --- Auth & User Management Views ---

def set_refresh_cookie(response, refresh_token):
    max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE,
        refresh_token,
        max_age=max_age,
        httponly=settings.JWT_COOKIE_HTTP_ONLY,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_REFRESH_COOKIE_PATH,
    )


def set_access_cookie(response, access_token):
    max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE,
        access_token,
        max_age=max_age,
        httponly=settings.JWT_COOKIE_HTTP_ONLY,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_ACCESS_COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )


def clear_access_cookie(response):
    response.delete_cookie(
        settings.JWT_ACCESS_COOKIE,
        path=settings.JWT_ACCESS_COOKIE_PATH,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the newly created user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response_data = {
            'refresh': refresh_token,
            'access': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
            }
        }

        response = Response(response_data, status=status.HTTP_201_CREATED)

        # Set cookies for access and refresh tokens
        set_access_cookie(response, access_token)
        set_refresh_cookie(response, refresh_token)

        return response

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Validate credentials using the serializer so we can enforce MFA when enabled.
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = getattr(serializer, 'user', None)

        # If user has MFA enabled, require MFA verification before issuing tokens.
        if user:
            try:
                mfa_config = MFAConfig.objects.get(user=user)
            except MFAConfig.DoesNotExist:
                mfa_config = None

            if mfa_config and mfa_config.is_enabled:
                # Do not issue tokens yet; client must call /auth/mfa/verify/ with issue_tokens=true
                return Response({'mfa_required': True, 'email': request.data.get('email')}, status=status.HTTP_200_OK)

        # No MFA required — issue tokens and set cookies.
        data = serializer.validated_data
        access_token = data.get('access')
        refresh_token = data.get('refresh')
        response = Response(data, status=status.HTTP_200_OK)
        if access_token:
            set_access_cookie(response, access_token)
        if refresh_token:
            set_refresh_cookie(response, refresh_token)

        # Log login activity
        try:
            if user:
                ct = ContentType.objects.get_for_model(user.__class__)
                ActivityLog.objects.create(
                    actor=user,
                    content_type=ct,
                    object_id=user.id,
                    action='user.login',
                    description='User logged in via email/password',
                )
        except Exception:
            pass
        return response


class CookieTokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh") or request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE
        )

        if not refresh_token:
            return Response(
                {"detail": "Refresh token cookie not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        access_token = serializer.validated_data.get("access")
        if access_token:
            set_access_cookie(response, access_token)
        if serializer.validated_data.get("refresh"):
            set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    class LogoutSerializer(serializers.Serializer):
        refresh = serializers.CharField(required=False)

    def post(self, request):
        serializer = self.LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh") or request.COOKIES.get(
            settings.JWT_REFRESH_COOKIE
        )
        response = Response(
            {"detail": "Logout successful."},
            status=status.HTTP_205_RESET_CONTENT
        )

        if not refresh_token:
            clear_access_cookie(response)
            clear_refresh_cookie(response)
            return response

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        clear_access_cookie(response)
        clear_refresh_cookie(response)
        # Log logout if user is authenticated
        try:
            if request.user and request.user.is_authenticated:
                ct = ContentType.objects.get_for_model(request.user.__class__)
                ActivityLog.objects.create(
                    actor=request.user,
                    content_type=ct,
                    object_id=request.user.id,
                    action='user.logout',
                    description='User logged out via API',
                )
        except Exception:
            pass
        return response

# --- Password Reset Views ---

class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Do not reveal whether a user exists for this email.
            return Response(
                {
                    'email': email,
                    'message': 'If the email exists, an OTP has been generated.',
                },
                status=status.HTTP_200_OK,
            )
        otp_code = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)

        plain_message = (
            f"Hello {user.username},\n\n"
            f"Your OTP for password reset is: {otp_code}\n"
            f"This OTP will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            "If you did not request this, ignore this email."
        )
        html_message = render_to_string(
            'accounts/emails/password_reset_otp.html',
            {
                'username': user.username,
                'otp_code': otp_code,
                'otp_expire_minutes': settings.OTP_EXPIRE_MINUTES,
            },
        )

        try:
            send_mail(
                subject='Your password reset OTP',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
                html_message=html_message,
            )
        except Exception:
            # In dev mode, still return OTP so frontend flow can continue without SMTP.
            if settings.OTP_DEV_RETURN_OTP:
                return Response(
                    {
                        'email': email,
                        'message': 'OTP generated, but email sending failed. Using dev OTP response.',
                        'expires_in_minutes': settings.OTP_EXPIRE_MINUTES,
                        'otp': otp_code,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response({'error': 'Failed to send OTP email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = {
            'email': email,
            'message': 'OTP generated successfully and sent to email.',
            'expires_in_minutes': settings.OTP_EXPIRE_MINUTES,
        }
        if settings.OTP_DEV_RETURN_OTP:
            response_data['otp'] = otp_code

        return Response(response_data, status=status.HTTP_200_OK)

class PasswordResetVerifyOTPView(APIView):
    def post(self, request):
        serializer = PasswordResetVerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_record = (
            PasswordResetOTP.objects.filter(user=user, otp_code=otp, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if otp_record is None or otp_record.is_expired():
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'OTP is valid.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_record = (
            PasswordResetOTP.objects.filter(user=user, otp_code=otp, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if otp_record is None or otp_record.is_expired():
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as exc:
            return Response({'error': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])

        return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)

# --- MFA Views ---

class MFASetupView(APIView):
    def post(self, request):
        serializer = MFASetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        mfa_config, _ = MFAConfig.objects.get_or_create(
            user=user,
            defaults={'method': 'authenticator'},
        )

        if not mfa_config.secret:
            mfa_config.secret = generate_mfa_secret()
            mfa_config.method = 'authenticator'
            mfa_config.is_enabled = False
            mfa_config.save(update_fields=['secret', 'method', 'is_enabled'])

        qr_url = generate_qr_url(user.email, mfa_config.secret)

        return Response(
            {
                'email': email,
                'method': mfa_config.method,
                'is_enabled': mfa_config.is_enabled,
                'qr_url': qr_url,
                'secret': mfa_config.secret,
            },
            status=status.HTTP_200_OK,
        )

class MFAVerifyView(APIView):
    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        token = serializer.validated_data['token']
        issue_tokens = serializer.validated_data.get('issue_tokens', False)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            mfa_config = MFAConfig.objects.get(user=user, method='authenticator')
        except MFAConfig.DoesNotExist:
            return Response({'error': 'MFA setup not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not mfa_config.secret:
            return Response({'error': 'MFA secret missing. Setup MFA first.'}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_mfa_token(mfa_config.secret, token):
            return Response({'error': 'Invalid MFA token.'}, status=status.HTTP_400_BAD_REQUEST)

        if not mfa_config.is_enabled:
            mfa_config.is_enabled = True
            mfa_config.save(update_fields=['is_enabled'])

        # Optionally issue JWT tokens (used when verifying during login flow)
        if issue_tokens:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            response = Response(
                {
                    'message': 'MFA verified and tokens issued.',
                    'access': access_token,
                    'refresh': refresh_token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': getattr(user, 'first_name', ''),
                        'last_name': getattr(user, 'last_name', ''),
                    },
                },
                status=status.HTTP_200_OK,
            )
            set_access_cookie(response, access_token)
            set_refresh_cookie(response, refresh_token)
            return response

        return Response({'message': 'MFA verified and enabled.'}, status=status.HTTP_200_OK)

# --- OAuth Views ---

class OAuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OAuthLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        provider = serializer.validated_data['provider']

        if provider == 'github':
            user_data = self._handle_github(code)
        elif provider == 'google':
            user_data = self._handle_google(code)
        else:
            return Response({'error': 'Unsupported provider.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user_data:
            return Response({'error': f'Failed to authenticate with {provider}.'}, status=status.HTTP_400_BAD_REQUEST)

        email = user_data.get('email')
        uid = user_data.get('id')
        name = user_data.get('name', '')

        if not email:
            return Response({'error': 'Email not provided by OAuth provider.'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0] + "_" + str(random.randint(1000, 9999)),
                'first_name': name.split(' ')[0] if name else '',
                'last_name': ' '.join(name.split(' ')[1:]) if name and len(name.split(' ')) > 1 else '',
            }
        )

        OAuthAccount.objects.get_or_create(
            user=user,
            provider=provider,
            defaults={'provider_user_id': str(uid)}
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        response = Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)

        # Set cookies
        set_access_cookie(response, str(refresh.access_token))
        set_refresh_cookie(response, str(refresh))

        # Log OAuth login activity
        try:
            ct = ContentType.objects.get_for_model(user.__class__)
            ActivityLog.objects.create(
                actor=user,
                content_type=ct,
                object_id=user.id,
                action=f'oauth.login.{provider}',
                description=f'User logged in via {provider}',
            )
        except Exception:
            pass

        return response

    def _handle_github(self, code):
        client_id = getattr(settings, 'GITHUB_CLIENT_ID', None)
        client_secret = getattr(settings, 'GITHUB_CLIENT_SECRET', None)
        
        if not client_id or not client_secret:
            # Fallback for dev if not configured
            return None

        # 1. Exchange code for token
        token_res = requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
            },
            headers={'Accept': 'application/json'}
        )
        token_data = token_res.json()
        access_token = token_data.get('access_token')
        if not access_token:
            return None

        # 2. Get user profile
        user_res = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {access_token}'}
        )
        return user_res.json()

    def _handle_google(self, code):
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', None)

        if not client_id or not client_secret:
            return None

        # 1. Exchange code for token
        token_res = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
            }
        )
        token_data = token_res.json()
        access_token = token_data.get('access_token')
        if not access_token:
            return None

        # 2. Get user info
        user_res = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        return user_res.json()



class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # If avatar was uploaded, set avatar_url to storage URL for convenience
        if profile.avatar:
            try:
                serializer_data = serializer.data
                avatar_field = profile.avatar.url
                profile.avatar_url = avatar_field
                profile.save(update_fields=['avatar_url'])
                serializer_data['avatar_url'] = avatar_field
                return Response(serializer_data)
            except Exception:
                pass

        return Response(serializer.data)
    
