from reservations.models import Reservation
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, DurationField, Avg


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
