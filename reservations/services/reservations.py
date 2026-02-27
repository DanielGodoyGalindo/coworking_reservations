import calendar
from django.db import transaction
from django.http import JsonResponse
from coworking_reservations import settings
from reservations import models
from reservations.models import Reservation
from django.utils import timezone
from datetime import datetime
from datetime import date, timedelta, time
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
# PermissionDenied throws 403


class ReservationOverlapError(Exception):
    pass


class ReservationConfirmationError(Exception):
    pass


@transaction.atomic
def create_reservation(*, idempotency_key, room, date, start_time, end_time, user):

    if date < timezone.localdate():
        raise ValueError("Cannot reserve in the past")
    validate_duration(date, start_time, end_time)

    existing = Reservation.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing

    if Reservation.overlapping_exists(room, date, start_time, end_time):
        raise ReservationOverlapError("Time slot already booked")

    try:
        reservation = Reservation.objects.create(
            idempotency_key=idempotency_key,
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status=Reservation.Status.PENDING,
            user=user,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
    except IntegrityError:
        reservation = Reservation.objects.get(idempotency_key=idempotency_key)
    return reservation


def get_available_slots(*, room, date, slot_minutes=30, minimum_minutes=60):

    OPENING_HOUR = time(settings.COWORKING_OPENING_HOUR)
    CLOSING_HOUR = time(settings.COWORKING_CLOSING_HOUR)

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
    current_start = OPENING_HOUR

    for reservation in reservations:
        if reservation.start_time > current_start:
            free_ranges.append((current_start, reservation.start_time))
        current_start = max(current_start, reservation.end_time)

    if current_start < CLOSING_HOUR:
        free_ranges.append((current_start, CLOSING_HOUR))

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


def validate_duration(date, start_time, end_time):

    start_dt = datetime.combine(date, start_time)
    end_dt = datetime.combine(date, end_time)

    duration_minutes = (end_dt - start_dt).total_seconds() / 60

    if duration_minutes < 60:
        raise ValueError("Minimum reservation is 60 minutes")

    if duration_minutes % 30 != 0:
        raise ValueError("Reservation must be in 30-minute increments")


def confirm_reservation(*, reservation, user):

    if reservation.user != user:
        raise PermissionDenied("You cannot confirm this reservation")

    if reservation.status != Reservation.Status.PENDING:
        raise ReservationConfirmationError("Only pending reservations can be confirmed")

    if reservation.date < timezone.localdate():
        raise ReservationConfirmationError("Cannot confirm past reservation")

    # change status to cancelled if is expired
    if reservation.expires_at and reservation.expires_at <= timezone.now():
        reservation.status = Reservation.Status.CANCELLED
        reservation.save()
        raise ReservationConfirmationError("Reservation has expired")

    reservation.status = Reservation.Status.CONFIRMED
    reservation.expires_at = None
    reservation.save()

    return reservation


##############
# Automation #
##############


def expire_pending_reservations():
    now = timezone.now()

    expired = Reservation.objects.filter(
        status=Reservation.Status.PENDING,
        expires_at__lte=now,
    )

    count = expired.update(status=Reservation.Status.CANCELLED)

    return count
