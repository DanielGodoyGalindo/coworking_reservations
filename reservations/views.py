from reservations.models import Reservation
from reservations.services.reservations import (
    get_user_reservation,
    get_user_reservations,
)
from rooms.models import Room
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm


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
    statuses = [value for value, label in Reservation.Status.choices]
    reservation = get_user_reservation(request.user, reservation_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Reservation.Status.choices):
            reservation.status = new_status
            reservation.save()

    return render(
        request,
        "reservations/reservation_details.html",
        {"reservation": reservation, "statuses": statuses},
    )


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})
