from reservations.models import Reservation
from django.utils import timezone


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
        status=Reservation.Status.PENDING,
        expires_at__lte=timezone.now(),
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


def conversion_rate():
    return None


def expiration_rate():
    return None


def average_time_to_confirmation():
    return None
