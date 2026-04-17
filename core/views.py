from django.contrib.auth import get_user_model
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from  .serializer import CurrentUserProfileSerializer 
from rest_framework import status 

User = get_user_model()

@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok"}) 


class CurrentUserProfileView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        )
    def patch(self, request):
        user = request.user 
        serializer = CurrentUserProfileSerializer(user, data=request.data ,  partial = True ) 

        if not serializer.is_valid(): 
            return Response(serializer.errors , status = status.HTTP_400_BAD_REQUEST) 
        
        #we can add image  field here and models 
        user.username = serializer.validated_data.get("username" , user.username)
        user.email = serializer.validated_data.get("email" , user.email) 
        user.first_name = serializer.validated_data.get("first_name" , user.first_name)
        user.last_name = serializer.validated_data.get("last_name" , user.last_name)

        user.save() 
        return Response({"message": "Profile updated successfully"} , status = status.HTTP_200_OK ) 
class UserDetailView(APIView): 
        authentication_classes = [JWTAuthentication, SessionAuthentication]
        permission_classes = [IsAuthenticated] 

        def get(self, request , user_id ): 
            try: 
                user = User.objects.get(id = user_id) 
            except User.DoesNotExist: 
                return Response({"error": "User not found"} , status = status.HTTP_404_NOT_FOUND) 
            
            return Response( 
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
            ) 

