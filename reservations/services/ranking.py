import calendar
from coworking_reservations import settings
from reservations.models import Reservation
from datetime import datetime
from datetime import date, time
from django.db.models import F, ExpressionWrapper, DurationField, Sum
from rooms.models import Room


def rooms_monthly_ranking(year, month):

    OPENING_HOUR = settings.COWORKING_OPENING_HOUR
    CLOSING_HOUR = settings.COWORKING_CLOSING_HOUR

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    daily_seconds = (
        datetime.combine(start_date, time(CLOSING_HOUR))
        - datetime.combine(start_date, time(OPENING_HOUR))
    ).total_seconds()

    total_days = (end_date - start_date).days + 1
    available_per_room = total_days * daily_seconds

    rooms = Room.objects.all()
    ranking = []

    for room in rooms:
        reservations = (
            Reservation.objects.filter(
                room=room,
                date__range=(start_date, end_date),
                status=Reservation.Status.CONFIRMED,
            )
            .annotate(
                duration=ExpressionWrapper(
                    F("end_time") - F("start_time"),
                    output_field=DurationField(),
                )
            )
            .aggregate(total=Sum("duration"))
        )

        occupied_seconds = (
            reservations["total"].total_seconds() if reservations["total"] else 0
        )

        occupancy = (
            occupied_seconds / available_per_room if available_per_room > 0 else 0
        )

        ranking.append(
            {
                "room": room,
                "occupancy": occupancy,
            }
        )

    ranking.sort(key=lambda x: x["occupancy"], reverse=True)

    return ranking


def best_performing_room():
    return None


def total_hours_per_room():
    return None
