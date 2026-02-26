from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from datetime import date as date_type
from rooms.models import Room
from reservations.services import (
    confirm_reservation,
    get_available_slots,
    create_reservation,
    ReservationOverlapError,
    ReservationConfirmationError,
)
import json
from datetime import date as date_type, time as time_type
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from reservations.models import Reservation
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


@require_GET
def availability_view(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    room_id = request.GET.get("room_id")
    date_str = request.GET.get("date")

    if not room_id or not date_str:
        error_response("room_id and date are required", 400)

    try:
        date = date_type.fromisoformat(date_str)
    except ValueError:
        error_response("Invalid date format (YYYY-MM-DD)", 400)

    room = get_object_or_404(Room, id=room_id)

    slots = get_available_slots(room=room, date=date)

    return JsonResponse(
        {
            "room_id": room.id,
            "name": room.name,
            "date": date.isoformat(),
            "slots": [
                {
                    "start": start.strftime("%H:%M"),
                    "end": end.strftime("%H:%M"),
                }
                for start, end in slots
            ],
        }
    )


@csrf_exempt
@require_POST
def create_reservation_view(request):

    if not request.user.is_authenticated:
        error_response("Authentication required", 401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response("Invalid JSON", 400)

    required_fields = {"room_id", "date", "start_time", "end_time"}
    if not required_fields.issubset(data):
        return error_response("Missing required fields", 400)

    try:
        date = date_type.fromisoformat(data["date"])
        start_time = time_type.fromisoformat(data["start_time"])
        end_time = time_type.fromisoformat(data["end_time"])
    except ValueError:
        return error_response("Invalid date or time format", 400)

    if start_time >= end_time:
        return error_response("start_time must be before end_time", 400)

    room = get_object_or_404(Room, id=data["room_id"])

    idempotency_key = request.headers.get("Idempotency-Key")

    if not idempotency_key:
        return error_response("Idempotency-Key header required", 400)

    try:
        reservation = create_reservation(
            idempotency_key=idempotency_key,
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
            user=request.user,
        )
    except ReservationOverlapError as e:
        return error_response(str(e), 409)

    except ValueError as e:
        return error_response(str(e), 400)

    return JsonResponse(
        {
            "id": reservation.id,
            "room_id": room.id,
            "date": reservation.date.isoformat(),
            "start_time": reservation.start_time.strftime("%H:%M"),
            "end_time": reservation.end_time.strftime("%H:%M"),
            "status": reservation.status,
        },
        status=201,
    )


@require_GET
def list_reservations_view(request):

    if not request.user.is_authenticated:
        return error_response("Authentication required", 401)

    # Only get reservations from authenticated user, only rooms related to user, and order by date
    # filter ==> select reservations where user = authenticated user
    # select_related ==> get reservations that has ForeignKey relationship
    # order_by ==> like sql
    reservations = (
        Reservation.objects.filter(user=request.user)
        .select_related("room")
        .order_by("date", "start_time")
    )

    data = [
        {
            "id": r.id,
            "room": r.room.name,
            "room_id": r.room.id,
            "date": r.date.isoformat(),
            "start_time": r.start_time.strftime("%H:%M"),
            "end_time": r.end_time.strftime("%H:%M"),
            "status": r.status,
        }
        for r in reservations
    ]

    return JsonResponse({"reservations": data})


@require_http_methods(["DELETE"])
def delete_reservation_view(request, reservation_id):

    if not request.user.is_authenticated:
        return error_response("Authentication required", 401)

    reservation = get_object_or_404(Reservation, id=reservation_id)

    if reservation.user != request.user:
        return error_response("Delete action forbidden", 403)

    if reservation.status == Reservation.Status.CANCELLED:
        return error_response("Reservation already cancelled", 400)

    if reservation.date < date_type.today():
        return error_response("Cannot cancel past reservations", 400)

    # hard delete
    # reservation.delete()

    # soft delete
    reservation.status = Reservation.Status.CANCELLED
    reservation.save()

    return JsonResponse({"message": "Reservation deleted"}, status=200)


def confirm_reservation_view(request, reservation_id):

    if not request.user.is_authenticated:
        return error_response("Authentication required", 401)

    reservation = get_object_or_404(Reservation, id=reservation_id)

    try:
        reservation = confirm_reservation(
            reservation=reservation,
            user=request.user,
        )

    except PermissionDenied as e:
        return error_response(str(e), 403)

    except ReservationOverlapError as e:
        return error_response(str(e), 409)

    except ReservationConfirmationError as e:
        return error_response(str(e), 400)

    return JsonResponse(
        {
            "id": reservation.id,
            "status": reservation.status,
        },
        status=200,
    )


def error_response(message, status_code):
    return JsonResponse({"error": message}, status=status_code)
