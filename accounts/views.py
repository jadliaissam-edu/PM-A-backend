from datetime import timedelta
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PasswordResetOTP

# Register 
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data): 
        user = User.objects.create_user(
            username=validated_data['username'], 
            email=validated_data['email'], 
            password=validated_data['password'],
             ) 
        return user 
    
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer 

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Do not reveal whether a user exists for this email.
            return Response({'message': 'If the email exists, an OTP has been generated.'}, status=status.HTTP_200_OK)

        otp_code = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)

        try:
            send_mail(
                subject='Your password reset OTP',
                message=(
                    f"Hello {user.username},\n\n"
                    f"Your OTP for password reset is: {otp_code}\n"
                    f"This OTP will expire in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
                    "If you did not request this, ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            return Response({'error': 'Failed to send OTP email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = {
            'message': 'OTP generated successfully and sent to email.',
            'expires_in_minutes': settings.OTP_EXPIRE_MINUTES,
        }
        if settings.OTP_DEV_RETURN_OTP:
            response_data['otp'] = otp_code

        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetVerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'error': 'email and otp are required.'}, status=status.HTTP_400_BAD_REQUEST)

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
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')

        if not email or not otp or not new_password:
            return Response(
                {'error': 'email, otp and new_password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

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




    