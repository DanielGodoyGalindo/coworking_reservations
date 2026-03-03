from reservations.models import Reservation
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DurationField, Avg
from rooms.models import Room
from datetime import datetime, time
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Value


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
    Returns average time (in seconds) it takes to confirm a reservation.
    """

    confirmed_reservations = Reservation.objects.filter(
        date__range=(start_date, end_date),
        status=Reservation.Status.CONFIRMED,
        confirmed_at__isnull=False,
    ).annotate(
        confirmation_time=ExpressionWrapper(
            F("confirmed_at") - F("created_at"), output_field=DurationField()
        )
    )

    avg_duration = confirmed_reservations.aggregate(avg=Avg("confirmation_time"))["avg"]

    if not avg_duration:
        return 0

    return avg_duration.total_seconds()


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
            Value(0),
        )
    )["total"]

    occupied_seconds = total_duration.total_seconds() if total_duration else 0

    return round((occupied_seconds / total_available_seconds) * 100, 2)
