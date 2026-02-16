from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from reservations import models
from reservations.models import Reservation
from django.utils import timezone
import datetime
from datetime import timedelta
from django.db.models import Q


class ReservationOverlapError(Exception):
    pass


@transaction.atomic
def create_reservation(*, room, date, start_time, end_time, user):

    validate_duration(date, start_time, end_time)

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
        expires_at=timezone.now() + timedelta(minutes=10),
    )


def get_available_slots(*, room, date, slot_minutes=30, minimum_minutes=60):

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

    # Calculate big ranges
    free_ranges = []
    current_start = OPEN_TIME

    for reservation in reservations:
        if reservation.start_time > current_start:
            free_ranges.append((current_start, reservation.start_time))
        current_start = max(current_start, reservation.end_time)

    if current_start < CLOSE_TIME:
        free_ranges.append((current_start, CLOSE_TIME))

    # Divide in slots
    slots = []

    for start, end in free_ranges:
        start_dt = datetime.datetime.combine(date, start)
        end_dt = datetime.datetime.combine(date, end)

        while start_dt + timedelta(minutes=slot_minutes) <= end_dt:
            total_available = (end_dt - start_dt).total_seconds() / 60

            if total_available >= minimum_minutes:
                slot_end = start_dt + timedelta(minutes=slot_minutes)

                slots.append(
                    (
                        start_dt.time(),
                        slot_end.time(),
                    )
                )

            start_dt += timedelta(minutes=slot_minutes)

    return slots


def confirm_reservation(reservation):
    reservation.status = Reservation.Status.CONFIRMED
    reservation.expires_at = None
    reservation.save()


def expire_pending_reservations():
    Reservation.objects.filter(
        status=Reservation.Status.PENDING,
        expires_at__lte=timezone.now(),
    ).update(status=Reservation.Status.CANCELLED)


def validate_duration(date, start_time, end_time):

    start_dt = datetime.datetime.combine(date, start_time)
    end_dt = datetime.datetime.combine(date, end_time)

    duration_minutes = (end_dt - start_dt).total_seconds() / 60

    if duration_minutes < 60:
        raise ValueError("Minimum reservation is 60 minutes")

    if duration_minutes % 30 != 0:
        raise ValueError("Reservation must be in 30-minute increments")
