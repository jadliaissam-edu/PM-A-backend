from  rest_framework import serializers 

class CurrentUserProfileSerializer(serializers.Serializer): 
    id = serializers.UUIDField(read_only=True) 
    username = serializers.CharField(read_only=True) 
    email = serializers.EmailField(read_only=True) 
    first_name = serializers.CharField(required=False, allow_blank=True) 
    last_name = serializers.CharField(required=False, allow_blank=True) 
    