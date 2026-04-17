
from datetime import timedelta
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializer import EmailTokenObtainPairSerializer

from .models import MFAConfig, PasswordResetOTP
from .services.mfa_service import generate_mfa_secret, generate_qr_url, verify_mfa_token
from .serializer import (
    MFASetupSerializer,
    MFAVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifyOTPSerializer,
    RegisterSerializer,
)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

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

        return Response({'message': 'MFA verified and enabled.'}, status=status.HTTP_200_OK)

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer