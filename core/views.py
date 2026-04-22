
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Space
from .serializers import SpaceSerializer

@api_view(["GET"])
def space_list(request):
    spaces = Space.objects.all()
    serializer = SpaceSerializer(spaces, many=True)
    return Response(serializer.data)