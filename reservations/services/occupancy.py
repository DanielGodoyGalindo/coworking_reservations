import calendar
from coworking_reservations import settings
from reservations.models import Reservation
from datetime import datetime
from datetime import date, timedelta, time
from django.db.models import F, ExpressionWrapper, DurationField, Sum
from rooms.models import Room


###################
# Occupancy rates #
###################


def occupancy_rate(room, date):
    """
    Returns percentage of room that was occupied on a given date
    """

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


def global_daily_occupancy(date):
    """
    Returns the global occupancy rate (0..1) for all rooms
    in the coworking on a given date.
    """

    OPENING_HOUR = time(settings.COWORKING_OPENING_HOUR)
    CLOSING_HOUR = time(settings.COWORKING_CLOSING_HOUR)

    rooms = Room.objects.all()
    available_seconds = 0
    occupied_seconds = 0

    for room in rooms:
        room_available_seconds = (
            datetime.combine(date, CLOSING_HOUR) - datetime.combine(date, OPENING_HOUR)
        ).total_seconds()
        available_seconds += room_available_seconds

        reservations = Reservation.objects.filter(
            room=room, date=date, status=Reservation.Status.CONFIRMED
        )

        for reservation in reservations:
            reservation_seconds = (
                datetime.combine(date, reservation.end_time)
                - datetime.combine(date, reservation.start_time)
            ).total_seconds()
            occupied_seconds += reservation_seconds

    if available_seconds == 0:
        return 0.0

    return occupied_seconds / available_seconds


def peak_day(year, month):
    """
    Returns the day with the highest global occupancy rate
    for the given year and month.

    Input: year and month

    Output:
    {
        "date": date,
        "occupancy_rate": float
    }
    """
    _, num_days = calendar.monthrange(year, month)

    peak = None
    max_rate = -1

    for day in range(1, num_days + 1):
        current_date = date(year, month, day)

        rate = global_daily_occupancy(current_date)

        if rate > max_rate:
            max_rate = rate
            peak = current_date

    if peak is None:
        return None

    return {
        "date": peak,
        "occupancy_rate": max_rate,
    }
