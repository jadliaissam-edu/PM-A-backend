from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

user = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)


class MFASetupSerializer(serializers.Serializer):
    email = serializers.EmailField()


class MFAVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(max_length=6)


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user_model = get_user_model()
        new_user = user_model.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return new_user    

from django.contrib.auth import authenticate

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        identifier = attrs.get("email")
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError(
                "Email and password are required"
            )

        matched_users = list(
            user.objects.filter(email=identifier).order_by("id")
        )

        valid_email_users = [
            candidate
            for candidate in matched_users
            if candidate.check_password(password) and getattr(candidate, "is_active", True)
        ]

        if len(valid_email_users) > 1:
            raise serializers.ValidationError(
                "Multiple accounts use this email. Please log in with your username."
            )

        if len(valid_email_users) == 1:
            user_obj = valid_email_users[0]
        elif matched_users:
            user_obj = None
        else:
            user_obj = authenticate(
                request=self.context.get("request"),
                username=identifier,
                password=password
            )

        if not user_obj:
            raise serializers.ValidationError(
                "No active account found with the given credentials"
            )

        self.user = user_obj
        data = self.get_token(user_obj)
        return {
            "refresh": str(data),
            "access": str(data.access_token),
            "username": user_obj.username,
            "email": user_obj.email,
        }
