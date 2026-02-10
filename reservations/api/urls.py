from django.urls import path
from .views import availability_view, create_reservation_view

urlpatterns = [
    path("availability/", availability_view, name="availability"),
    path("reservations/", create_reservation_view),
]