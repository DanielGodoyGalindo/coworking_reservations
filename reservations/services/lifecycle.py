from reservations.models import Reservation
from django.db.models import F, ExpressionWrapper, DurationField, Avg
from rooms.models import Room
from datetime import datetime, time
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Value
from datetime import timedelta, date


def total_reservations(start_date, end_date):
    """
    Returns the total number of reservations in a date range.
    """
    return Reservation.objects.filter(
        date__range=(start_date, end_date),
        status__in=[
            Reservation.Status.CONFIRMED,
            Reservation.Status.PENDING,
            Reservation.Status.CANCELLED,
        ],
    ).count()


def confirmed_count(start_date, end_date):
    """
    Returns the number of confirmed reservations
    within the given date range.
    """
    return Reservation.objects.filter(
        date__range=(start_date, end_date),
        status=Reservation.Status.CONFIRMED,
    ).count()


def expired_count(start_date, end_date):
    """
    Returns the number of expired reservations
    within the given date range.
    """
    return Reservation.objects.filter(
        date__range=(start_date, end_date),
        status=Reservation.Status.EXPIRED,
    ).count()


def pending_count(start_date, end_date):
    """
    Returns the number of pending reservations
    within the given date range.
    """
    return Reservation.objects.filter(
        date__range=(start_date, end_date),
        status=Reservation.Status.PENDING,
    ).count()


def conversion_rate(start_date, end_date):
    """
    Percentage of reservations that end up confirmed.
    """

    total = Reservation.objects.filter(date__range=(start_date, end_date)).count()

    if total == 0:
        return 0

    confirmed = Reservation.objects.filter(
        date__range=(start_date, end_date), status=Reservation.Status.CONFIRMED
    ).count()

    return confirmed / total


def expiration_rate(start_date, end_date):
    """
    Percentage of reservations that expire.
    """

    total = Reservation.objects.filter(date__range=(start_date, end_date)).count()

    if total == 0:
        return 0

    expired = Reservation.objects.filter(
        date__range=(start_date, end_date), status=Reservation.Status.EXPIRED
    ).count()

    return expired / total


def average_time_to_confirmation(start_date, end_date):
    """
    Avg time in seconds from created to confirmed reservations
    """

    confirmed_reservations = Reservation.objects.filter(
        date__range=(start_date, end_date),
        status=Reservation.Status.CONFIRMED,
        confirmed_at__isnull=False,
        created_at__isnull=False,
    ).values_list("created_at", "confirmed_at")

    total_seconds = 0
    count = 0

    for created, confirmed in confirmed_reservations:
        delta = confirmed - created
        total_seconds += delta.total_seconds()
        count += 1

    if count == 0:
        return 0

    return total_seconds / count


def global_utilization(start_date, end_date):
    """
    Returns global utilization percentage across all rooms
    in a given date range.
    """

    OPENING_HOUR = time(settings.COWORKING_OPENING_HOUR)
    CLOSING_HOUR = time(settings.COWORKING_CLOSING_HOUR)

    daily_available_seconds = (
        datetime.combine(start_date, CLOSING_HOUR)
        - datetime.combine(start_date, OPENING_HOUR)
    ).total_seconds()

    number_of_days = (end_date - start_date).days + 1
    total_rooms = Room.objects.count()

    total_available_seconds = daily_available_seconds * number_of_days * total_rooms

    if total_available_seconds == 0:
        return 0

    total_duration = Reservation.objects.filter(
        date__range=(start_date, end_date), status=Reservation.Status.CONFIRMED
    ).aggregate(
        total=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("end_time") - F("start_time"),
                    output_field=DurationField(),
                )
            ),
            Value(timedelta(0), output_field=DurationField()),
        )
    )["total"]

    occupied_seconds = total_duration.total_seconds() if total_duration else 0

    return round((occupied_seconds / total_available_seconds) * 100, 2)


def average_booking_duration(start_date, end_date):
    """
    Average duration of reservations in seconds
    """

    reservations = Reservation.objects.filter(
        date__range=(start_date, end_date),
        status=Reservation.Status.CONFIRMED,
    ).values_list("start_time", "end_time")

    total_seconds = 0
    count = 0

    for start, end in reservations:
        if start and end:
            start_dt = datetime.combine(date.today(), start)
            end_dt = datetime.combine(date.today(), end)
            total_seconds += (end_dt - start_dt).total_seconds()
            count += 1

    if count == 0:
        return 0

    return total_seconds / count


def average_booking_lead_time(start_date, end_date):
    """
    Average time between reservation creation and reservation date
    """

    reservations = Reservation.objects.filter(
        date__range=(start_date, end_date),
        created_at__isnull=False,
    ).values_list("created_at", "date")

    total_seconds = 0
    count = 0

    for created, reservation_date in reservations:
        if created and reservation_date:
            delta = reservation_date - created.date()
            total_seconds += delta.total_seconds()
            count += 1

    if count == 0:
        return 0

    return total_seconds / count
