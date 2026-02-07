from django.core.exceptions import ValidationError
from django.db import transaction
from reservations.models import Reservation
import datetime


@transaction.atomic
def create_reservation(*, user, room, date, start_time, end_time):
    # Time validation
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time.")

    # Overlapping (ignore CANCELLED)
    overlapping_exists = Reservation.objects.filter(
        room=room,
        date=date,
        status__in=[
            Reservation.Status.PENDING,
            Reservation.Status.CONFIRMED,
        ],
        # existing reservations start time is less or equal than new reservation end time
        # e.g. existing 13:00-15:00 and new 12:00h-14:00h --> 13:00 < 14:00 (overlap)
        start_time__lt=end_time,
        # existing reservations end time is greater or equal than new reservation start time
        # e.g. existing 9:00-11:00 and new 10:00h-12:00h --> 11:00 > 10:00 (overlap)
        end_time__gt=start_time,
    ).exists()

    if overlapping_exists:
        raise ValidationError("The room is already reserved for this time slot.")

    # Create reservation
    reservation = Reservation.objects.create(
        user=user,
        room=room,
        date=date,
        start_time=start_time,
        end_time=end_time,
    )
    return reservation


def get_available_slots(*, room, date, minimum_minutes=None):
    OPEN_TIME = datetime.time(8, 0)
    CLOSE_TIME = datetime.time(18, 0)

    reservations = Reservation.objects.filter(
        room=room,
        date=date,
        status__in=[
            Reservation.Status.PENDING,
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
