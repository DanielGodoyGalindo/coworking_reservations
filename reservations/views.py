from django.shortcuts import render
from reservations.models import Reservation
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

    reservations = (
        Reservation.objects.filter(user=request.user)
        .select_related("room")
        .order_by("date", "start_time")
    )

    return render(
        request, "reservations/my_reservations.html", {"reservations": reservations}
    )
