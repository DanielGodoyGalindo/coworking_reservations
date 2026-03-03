import calendar
from coworking_reservations import settings
from reservations.models import Reservation
from datetime import datetime
from datetime import date, time
from django.db.models import F, Q, ExpressionWrapper, DurationField, Sum, Value
from rooms.models import Room
from django.db.models.functions import Coalesce


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


def best_performing_room(start_date, end_date):
    """
    Returns the room with the highest total occupied time.
    """

    rooms = Room.objects.annotate(
        total_occupied=Sum(
            ExpressionWrapper(
                F("reservation__end_time") - F("reservation__start_time"),
                output_field=DurationField(),
            ),
            filter=(
                Q(reservation__date__range=(start_date, end_date))
                & Q(reservation__status=Reservation.Status.CONFIRMED)
            ),
        )
    ).order_by("-total_occupied")

    return rooms.first()


def total_hours_per_room(start_date, end_date):
    """
    Returns total occupied hours per room in a date range.
    """

    rooms = Room.objects.annotate(
        total_duration=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("reservation__end_time") - F("reservation__start_time"),
                    output_field=DurationField(),
                ),
                filter=(
                    Q(reservation__date__range=(start_date, end_date))
                    & Q(reservation__status=Reservation.Status.CONFIRMED)
                ),
            ),
            Value(0),
        )
    )

    result = []

    for room in rooms:
        hours = room.total_duration.total_seconds() / 3600 if room.total_duration else 0

        result.append(
            {
                "room_id": room.id,
                "room_name": room.name,
                "total_hours": round(hours, 2),
            }
        )

    return result


def top_3_rooms(start_date, end_date):
    rooms = Room.objects.annotate(
        total_occupied=Sum(
            ExpressionWrapper(
                F("reservation__end_time") - F("reservation__start_time"),
                output_field=DurationField(),
            ),
            filter=(
                Q(reservation__date__range=(start_date, end_date))
                & Q(reservation__status=Reservation.Status.CONFIRMED)
            ),
        )
    ).order_by("-total_occupied")

    return rooms[:3]


def utilization_percentage_per_room(start_date, end_date):
    """
    Returns utilization percentage per room in a date range.
    """

    OPENING_HOUR = time(settings.COWORKING_OPENING_HOUR)
    CLOSING_HOUR = time(settings.COWORKING_CLOSING_HOUR)

    daily_available_seconds = (
        datetime.combine(start_date, CLOSING_HOUR)
        - datetime.combine(start_date, OPENING_HOUR)
    ).total_seconds()

    number_of_days = (end_date - start_date).days + 1
    total_available_seconds = daily_available_seconds * number_of_days

    rooms = Room.objects.annotate(
        total_duration=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("reservation__end_time") - F("reservation__start_time"),
                    output_field=DurationField(),
                ),
                filter=(
                    Q(reservation__date__range=(start_date, end_date))
                    & Q(reservation__status=Reservation.Status.CONFIRMED)
                ),
            ),
            Value(0),
        )
    )

    result = []

    for room in rooms:
        occupied_seconds = (
            room.total_duration.total_seconds() if room.total_duration else 0
        )

        utilization = (
            occupied_seconds / total_available_seconds
            if total_available_seconds > 0
            else 0
        )

        result.append(
            {
                "room_id": room.id,
                "room_name": room.name,
                "utilization_percentage": round(utilization * 100, 2),
            }
        )

    return result
