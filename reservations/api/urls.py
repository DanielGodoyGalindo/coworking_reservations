from django.urls import path

from reservations.views import dashboard_page, dashboard2_view
from .views import (
    availability_view,
    confirm_reservation_view,
    create_reservation_view,
    delete_reservation_view,
    list_reservations_view,
    DashboardView,
    GlobalDailyOccupancyView,
    monthlyOccupancyRate,
    roomsMonthlyRankingView,
)

urlpatterns = [
    path("availability/", availability_view),
    path("reservations/", create_reservation_view),
    path("my-reservations/", list_reservations_view),
    path("reservations/<int:reservation_id>/", delete_reservation_view),
    path("reservations/<int:reservation_id>/confirm/", confirm_reservation_view),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(
        "dashboard2/global-daily-occupancy/",
        GlobalDailyOccupancyView.as_view(),
        name="global-daily-occupancy",
    ),
    path(
        "dashboard2/rooms-monthly-ranking/",
        roomsMonthlyRankingView.as_view(),
        name="rooms-monthly-ranking",
    ),
    path("dashboard2/monthly-occupancy-rate/",
         monthlyOccupancyRate.as_view(),
         name="monthly-occupancy-rate"),
]
