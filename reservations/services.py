from django.core.exceptions import ValidationError
from django.db import transaction
from reservations.models import Reservation
import datetime


class ReservationOverlapError(Exception):
    pass


@transaction.atomic
def create_reservation(*, room, date, start_time, end_time, user=None):
    overlapping_exists = Reservation.objects.filter(
        room=room,
        date=date,
        status__in=[
            Reservation.Status.PENDING,
            Reservation.Status.CONFIRMED,
        ],
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).exists()

    if overlapping_exists:
        raise ReservationOverlapError("Time slot is not available")

    return Reservation.objects.create(
        room=room,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status=Reservation.Status.CONFIRMED,
        user=user,
    )


def get_available_slots(*, room, date, minimum_minutes=None):
    OPEN_TIME = datetime.time(8, 0)
    CLOSE_TIME = datetime.time(18, 0)

    reservations = Reservation.objects.filter(
        room=room,
        date=date,
        status__in=[
            Reservation.Status.CONFIRMED,
        ],
    ).order_by("start_time")

    available_slots = []
    current_start = OPEN_TIME

    def slot_is_long_enough(start, end):
        if minimum_minutes is None:
            return True

        start_dt = datetime.datetime.combine(date, start)
        end_dt = datetime.datetime.combine(date, end)

        duration = (end_dt - start_dt).total_seconds() / 60
        return duration >= minimum_minutes

    for reservation in reservations:
        if reservation.start_time > current_start:
            if slot_is_long_enough(current_start, reservation.start_time):
                available_slots.append((current_start, reservation.start_time))
        current_start = max(current_start, reservation.end_time)

    if current_start < CLOSE_TIME:
        if slot_is_long_enough(current_start, CLOSE_TIME):
            available_slots.append((current_start, CLOSE_TIME))

    return available_slots
