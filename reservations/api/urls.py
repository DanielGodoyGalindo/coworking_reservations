from django.urls import path
from .views import (
    availability_view,
    confirm_reservation_view,
    create_reservation_view,
    delete_reservation_view,
    list_reservations_view,
)

urlpatterns = [
    path("availability/", availability_view),
    path("reservations/", create_reservation_view),
    path("my-reservations/", list_reservations_view),
    path("reservations/<int:reservation_id>/", delete_reservation_view),
    path("reservations/<int:reservation_id>/confirm/", confirm_reservation_view),
]
