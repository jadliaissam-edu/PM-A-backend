# urls.py
from django.urls import path

from core.views import space_list
urlpatterns = [
    path("api/spaces/", space_list),
]