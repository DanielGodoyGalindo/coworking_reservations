from reservations.services.lifecycle import (
    average_booking_duration,
    average_booking_lead_time,
    average_time_to_confirmation,
    conversion_rate,
    expiration_rate,
    global_utilization,
    total_reservations,
)
from reservations.services.occupancy import most_used_time_slot, peak_day
from reservations.services.ranking import (
    top_3_rooms,
    total_hours_per_room,
    utilization_percentage_per_room,
)


def dashboard_metrics(start_date, end_date):

    top_rooms = top_3_rooms(start_date, end_date)

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": (end_date - start_date).days + 1,
        },
        "metrics": {
            "occupancy": {
                "global_utilization_percentage": global_utilization(
                    start_date, end_date
                ),
                "peak_day": peak_day(start_date.year, start_date.month),
                "most_used_time_slot": most_used_time_slot(start_date, end_date),
                "top_3_rooms": [
                    {"id": room.id, "name": room.name} for room in top_rooms
                ],
            },
            "lifecycle": {
                "total_reservations": total_reservations(start_date, end_date),
                "conversion_rate": conversion_rate(start_date, end_date),
                "expiration_rate": expiration_rate(start_date, end_date),
                "avg_time_to_confirmation_seconds": average_time_to_confirmation(
                    start_date, end_date
                ),
                "avg_booking_duration_seconds": average_booking_duration(
                    start_date, end_date
                ),
                "avg_booking_lead_time_seconds": average_booking_lead_time(
                    start_date, end_date
                ),
            },
            "rooms": {
                "total_hours_per_room": total_hours_per_room(start_date, end_date),
                "utilization_per_room": utilization_percentage_per_room(
                    start_date, end_date
                ),
            },
        },
    }
