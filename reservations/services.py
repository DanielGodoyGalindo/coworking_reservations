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
from django.core.exceptions import PermissionDenied
from django.db.models import F, ExpressionWrapper, DurationField, Sum

from rooms.models import Room
# PermissionDenied throws 403


class ReservationOverlapError(Exception):
    pass


class ReservationConfirmationError(Exception):
    pass


@transaction.atomic
def create_reservation(*, room, date, start_time, end_time, user):

    (Reservation.objects.select_for_update().filter(room=room, date=date))

    validate_duration(date, start_time, end_time)

    if Reservation.overlapping_exists(room, date, start_time, end_time):
        raise ReservationOverlapError("Time slot already booked")

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


def confirm_reservation(*, reservation, user):

    if reservation.user != user:
        raise PermissionDenied("You cannot confirm this reservation")

    if reservation.status != Reservation.Status.PENDING:
        raise ReservationConfirmationError("Only pending reservations can be confirmed")

    # change status to cancelled if is expired
    if reservation.expires_at and reservation.expires_at <= timezone.now():
        reservation.status = Reservation.Status.CANCELLED
        reservation.save()
        raise ReservationConfirmationError("Reservation has expired")

    reservation.status = Reservation.Status.CONFIRMED
    reservation.expires_at = None
    reservation.save()

    return reservation


###################
# Occupancy rates #
###################


def occupancy_rate(room, date):

    OPENING_HOUR = time(settings.COWORKING_OPENING_HOUR)
    CLOSING_HOUR = time(settings.COWORKING_CLOSING_HOUR)

    total_available_seconds = (
        datetime.combine(date, CLOSING_HOUR) - datetime.combine(date, OPENING_HOUR)
    ).total_seconds()

    reservations = Reservation.objects.filter(
        room=room,
        date=date,
        status=Reservation.Status.CONFIRMED,
    )

    occupied_seconds = 0

    for r in reservations:
        delta = (
            datetime.combine(date, r.end_time) - datetime.combine(date, r.start_time)
        ).total_seconds()
        occupied_seconds += delta

    if total_available_seconds == 0:
        return 0

    return occupied_seconds / total_available_seconds


def monthly_occupancy_rate(room, year, month):

    OPENING_HOUR = time(settings.COWORKING_OPENING_HOUR)
    CLOSING_HOUR = time(settings.COWORKING_CLOSING_HOUR)

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    current = start_date
    working_days = 0

    while current <= end_date:
        if current.weekday() < 5:
            working_days += 1
        current += timedelta(days=1)

    daily_seconds = (
        datetime.combine(start_date, CLOSING_HOUR)
        - datetime.combine(start_date, OPENING_HOUR)
    ).total_seconds()

    total_available_seconds = working_days * daily_seconds

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

    if total_available_seconds == 0:
        return 0

    return occupied_seconds / total_available_seconds


def global_monthly_occupancy(year, month):

    OPENING_HOUR = settings.COWORKING_OPENING_HOUR
    CLOSING_HOUR = settings.COWORKING_CLOSING_HOUR

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    total_rooms = Room.objects.count()

    daily_seconds = (
        datetime.combine(start_date, time(CLOSING_HOUR))
        - datetime.combine(start_date, time(OPENING_HOUR))
    ).total_seconds()

    total_days = (end_date - start_date).days + 1
    total_available_seconds = total_days * daily_seconds * total_rooms

    reservations = (
        Reservation.objects.filter(
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

    if total_available_seconds == 0:
        return 0

    return occupied_seconds / total_available_seconds


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
