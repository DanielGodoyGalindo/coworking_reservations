from django.urls import path
from .views import availability_view

urlpatterns = [
    path("availability/", availability_view, name="availability"),
]