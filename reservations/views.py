import uuid

from django.shortcuts import render
from reservations.services.reservations import create_reservation_service
from rooms.models import Room
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


# Create your views here.
@login_required
def dashboard_page(request):
    return render(request, "dashboard.html")


@login_required
def dashboard2_view(request):
    rooms = Room.objects.all()
    return render(request, "dashboard2.html", {"rooms": rooms})


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def create_reservation_html_view(request):
    if request.method == "POST":
        try:
            reservation = create_reservation_service(
                idempotency_key=str(uuid.uuid4()),
                room=request.POST["room"],
                date=request.POST["date"],
                start_time=request.POST["start_time"],
                end_time=request.POST["end_time"],
                user=request.user,
            )
            return redirect("my_reservations")
        except Exception as e:
            return render(request, "reservations/create_reservation.html", {"error": str(e)})
    return render(request, "reservations/create_reservation.html")
