from django.urls import path
from .views import availability_view, create_reservation_view, list_reservations_view

urlpatterns = [
    path("availability/", availability_view),
    path("reservations/", create_reservation_view),
    path("my-reservations/", list_reservations_view),
]