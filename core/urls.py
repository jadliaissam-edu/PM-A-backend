from django.urls import path

from core.views import space_list
urlpatterns = [
    path("spaces/", space_list),
]
