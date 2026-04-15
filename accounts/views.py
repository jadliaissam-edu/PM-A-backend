from django.shortcuts import render
from django.contrib.auth.tokens import default_token_generator 
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode 
from django.utils.encoding import force_bytes, force_str 
from rest_framework import serializers 
from rest_framework import generics
from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from django.contrib.auth.models import User 

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

#Rest Password 
class PasswordResetRequestView(APIView): 
    def post(self, request) : 
        email = request.data.get('email') 
        if not email: 
            return Response({'error': 'Email is Essential'}, status=status.HTTP_400_BAD_REQUEST )

        try: 
            user = User.objects.get(email=email) 
        except User.DoesNotExist: 
            return Response({'error': 'system error'}, status=status.HTTP_404_NOT_FOUND) 
        uid = urlsafe_base64_encode(force_bytes(user.pk)) 
        token = default_token_generator.make_token(user) 
        # in the  feature we will made obfuscation here to make the link more secure 
        reset_link = f"http://localhost:83000/reset-password/{uid}/{token}/"

        return  Response ({
            "message" : "Reset password link"
            "reset_link" : reset_link 
        })
class PasswordResetConfirmView(APIView): 
    def post (self , request ) 
    # this  feature ip  up class will  need  to  reobfuscation  here 
    uid = request.data.get('uid') 
    token = request.data.get('token') 
    new_password = request.data.get('new_password') 

    try: 
        uid = force_str(urlsafe_base64_decode(uid)) 
        user = User.objects.get(pk=uid) 
    except (Response ({"error" : "invalid user link"}, status=status.HTTP_400_BAD_REQUEST)) 
    if  not default_token_generator.check_token(user,token):
        return Response({"error" : "invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST )

    user.set_password(new_password) 
    user.save() 
    return Response({"message" : "password reset successful"}, status=status.HTTP_200_OK) 




    