from django.core.exceptions import ValidationError
from django.db import transaction

from reservations.models import Reservation


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