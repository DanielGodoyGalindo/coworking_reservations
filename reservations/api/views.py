from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from datetime import date as date_type

from rooms.models import Room
from reservations.services import get_available_slots


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