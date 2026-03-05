import calendar
from reservations.models import Reservation
from rooms.models import Room
from datetime import datetime, time, timedelta, date
from coworking_reservations import settings


def rooms_monthly_ranking(year, month):
    OPENING_HOUR = settings.COWORKING_OPENING_HOUR
    CLOSING_HOUR = settings.COWORKING_CLOSING_HOUR

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    daily_seconds = (CLOSING_HOUR - OPENING_HOUR) * 3600
    total_days = (end_date - start_date).days + 1
    available_per_room = daily_seconds * total_days

    ranking = []

    for room in Room.objects.all():
        reservations = Reservation.objects.filter(
            room=room,
            date__range=(start_date, end_date),
            status=Reservation.Status.CONFIRMED,
            start_time__isnull=False,
            end_time__isnull=False,
        ).values_list("start_time", "end_time")

        total_seconds = sum(
            (
                datetime.combine(date.today(), end)
                - datetime.combine(date.today(), start)
            ).total_seconds()
            for start, end in reservations
            if start and end
        )
        occupancy = total_seconds / available_per_room if available_per_room > 0 else 0

        ranking.append({"room": room, "occupancy": occupancy})

    ranking.sort(key=lambda x: x["occupancy"], reverse=True)
    return ranking


def best_performing_room(start_date, end_date):
    rooms_data = []

    for room in Room.objects.all():
        reservations = Reservation.objects.filter(
            room=room,
            date__range=(start_date, end_date),
            status=Reservation.Status.CONFIRMED,
            start_time__isnull=False,
            end_time__isnull=False,
        ).values_list("start_time", "end_time")

        total_seconds = sum(
            (
                datetime.combine(date.today(), end)
                - datetime.combine(date.today(), start)
            ).total_seconds()
            for start, end in reservations
            if start and end
        )
        rooms_data.append((room, total_seconds))

    if not rooms_data:
        return None

    # Ordenamos por tiempo total ocupado
    rooms_data.sort(key=lambda x: x[1], reverse=True)
    return rooms_data[0][0]


def top_3_rooms(start_date, end_date):
    rooms_data = []

    for room in Room.objects.all():
        reservations = Reservation.objects.filter(
            room=room,
            date__range=(start_date, end_date),
            status=Reservation.Status.CONFIRMED,
            start_time__isnull=False,
            end_time__isnull=False,
        ).values_list("start_time", "end_time")

        total_seconds = sum(
            (
                datetime.combine(date.today(), end)
                - datetime.combine(date.today(), start)
            ).total_seconds()
            for start, end in reservations
            if start and end
        )
        rooms_data.append((room, total_seconds))

    rooms_data.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in rooms_data[:3]]


def utilization_percentage_per_room(start_date, end_date):
    OPENING_HOUR = settings.COWORKING_OPENING_HOUR
    CLOSING_HOUR = settings.COWORKING_CLOSING_HOUR

    daily_seconds = (CLOSING_HOUR - OPENING_HOUR) * 3600
    total_days = (end_date - start_date).days + 1
    total_available_seconds = daily_seconds * total_days

    result = []

    for room in Room.objects.all():
        reservations = Reservation.objects.filter(
            room=room,
            date__range=(start_date, end_date),
            status=Reservation.Status.CONFIRMED,
            start_time__isnull=False,
            end_time__isnull=False,
        ).values_list("start_time", "end_time")

        total_seconds = sum(
            (
                datetime.combine(date.today(), end)
                - datetime.combine(date.today(), start)
            ).total_seconds()
            for start, end in reservations
            if start and end
        )
        utilization = (
            total_seconds / total_available_seconds
            if total_available_seconds > 0
            else 0
        )

        result.append(
            {
                "room_id": room.id,
                "room_name": room.name,
                "utilization_percentage": round(utilization * 100, 2),
            }
        )

    return result


def total_hours_per_room(start_date, end_date):

    result = []

    rooms = Room.objects.all()

    for room in rooms:
        reservations = Reservation.objects.filter(
            room=room,
            date__range=(start_date, end_date),
            status=Reservation.Status.CONFIRMED,
            start_time__isnull=False,
            end_time__isnull=False,
        ).values_list("start_time", "end_time")

        total_seconds = 0

        for start, end in reservations:
            if start and end:
                start_dt = datetime.combine(date.today(), start)
                end_dt = datetime.combine(date.today(), end)

                delta = end_dt - start_dt
                total_seconds += delta.total_seconds()

                total_hours = round(total_seconds / 3600, 2)

        result.append(
            {"room_id": room.id, "room_name": room.name, "total_hours": total_hours}
        )

    return result
