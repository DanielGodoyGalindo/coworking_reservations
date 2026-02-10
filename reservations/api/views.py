from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from datetime import date as date_type
from rooms.models import Room
from reservations.services import (
    get_available_slots,
    create_reservation,
    ReservationOverlapError,
)
import json
from datetime import date as date_type, time as time_type
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@require_GET
def availability_view(request):
    room_id = request.GET.get("room_id")
    date_str = request.GET.get("date")

    if not room_id or not date_str:
        return JsonResponse(
            {"error": "room_id and date are required"},
            status=400,
        )

    try:
        date = date_type.fromisoformat(date_str)
    except ValueError:
        return JsonResponse(
            {"error": "Invalid date format (YYYY-MM-DD)"},
            status=400,
        )

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
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )

    required_fields = {"room_id", "date", "start_time", "end_time"}
    if not required_fields.issubset(data):
        return JsonResponse(
            {"error": "Missing required fields"},
            status=400,
        )

    try:
        date = date_type.fromisoformat(data["date"])
        start_time = time_type.fromisoformat(data["start_time"])
        end_time = time_type.fromisoformat(data["end_time"])
    except ValueError:
        return JsonResponse(
            {"error": "Invalid date or time format"},
            status=400,
        )

    if start_time >= end_time:
        return JsonResponse(
            {"error": "start_time must be before end_time"},
            status=400,
        )

    room = get_object_or_404(Room, id=data["room_id"])

    try:
        reservation = create_reservation(
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
        )
    except ReservationOverlapError as e:
        return JsonResponse(
            {"error": str(e)},
            status=409,
        )

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
