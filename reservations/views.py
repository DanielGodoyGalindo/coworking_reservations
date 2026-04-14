import uuid

from django.shortcuts import render
from reservations.models import Reservation
from reservations.services.reservations import (
    create_reservation_service,
    get_available_slots,
)
from rooms.models import Room
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
import datetime


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
    slots = None

    room_id = request.GET.get("room")
    date_str = request.GET.get("date")

    if room_id and date_str:
        try:
            room = Room.objects.get(id=room_id)
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            slots = get_available_slots(room=room, date=date)
        except Exception as e:
            print("Error calculando slots:", e)

    if request.method == "POST":
        try:
            date = datetime.datetime.strptime(request.POST["date"], "%Y-%m-%d").date()
            start_time = datetime.datetime.strptime(
                request.POST["start_time"], "%H:%M"
            ).time()
            end_time = datetime.datetime.strptime(
                request.POST["end_time"], "%H:%M"
            ).time()
            room = Room.objects.get(id=request.POST["room"])

            create_reservation_service(
                idempotency_key=str(uuid.uuid4()),
                room=room,
                date=date,
                start_time=start_time,
                end_time=end_time,
                user=request.user,
            )
            return redirect("my_reservations")

        except Exception as e:
            return render(
                request,
                "reservations/create_reservation.html",
                {
                    "rooms": rooms,
                    "available_slots": slots,
                    "error": str(e),
                },
            )

    return render(
        request,
        "reservations/create_reservation.html",
        {
            "rooms": rooms,
            "available_slots": slots,
        },
    )


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
