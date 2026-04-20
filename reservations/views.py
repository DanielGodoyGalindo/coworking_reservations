from django.shortcuts import render
from reservations.api.views import list_reservations_view
from reservations.models import Reservation
from reservations.services.reservations import (
    get_user_reservation,
    get_user_reservations,
)
from rooms.models import Room
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect


# Create your views here.
@staff_member_required
def dashboard_page(request):
    return render(request, "dashboard.html")


@staff_member_required
def dashboard2_view(request):
    rooms = Room.objects.all()
    return render(request, "dashboard2.html", {"rooms": rooms})


@login_required
def create_reservation_html_view(request):
    rooms = Room.objects.all()
    return render(request, "reservations/create_reservation.html", {"rooms": rooms})


@login_required
def my_reservations_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    reservations = get_user_reservations(request.user)
    return render(
        request, "reservations/my_reservations.html", {"reservations": reservations}
    )


@login_required
def my_reservation_info_view(request, reservation_id):
    reservation = get_user_reservation(request.user, reservation_id)
    return render(
        request,
        "reservations/reservation_details.html",
        {"reservation": reservation},
    )
