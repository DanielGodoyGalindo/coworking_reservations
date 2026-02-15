from django.core.exceptions import ValidationError
from django.db import transaction
from reservations import models
from reservations.models import Reservation
from django.utils import timezone
import datetime
from django.db.models import Q


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
        status=Reservation.Status.PENDING,
        user=user,
        expires_at=timezone.now()
        + datetime.timedelta(minutes=10),  # status pending and 10 minutes to expire
    )


def get_available_slots(*, room, date, minimum_minutes=None):
    OPEN_TIME = datetime.time(8, 0)
    CLOSE_TIME = datetime.time(18, 0)
    now = timezone.now()

    reservations = (
        Reservation.objects.filter(
            room=room,
            date=date,
        )
        .filter(
            Q(status=Reservation.Status.CONFIRMED)
            | Q(
                status=Reservation.Status.PENDING,
                expires_at__gt=now,
            )
        )
        .order_by("start_time")
    )

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


def confirm_reservation(reservation):
    reservation.status = Reservation.Status.CONFIRMED
    reservation.expires_at = None
    reservation.save()


def expire_pending_reservations():
    Reservation.objects.filter(
        status=Reservation.Status.PENDING,
        expires_at__lte=timezone.now(),
    ).update(status=Reservation.Status.CANCELLED)
