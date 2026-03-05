import random
from datetime import datetime, timedelta, time

from django.core.management.base import BaseCommand
from rooms.models import Room
from reservations.models import Reservation


class Command(BaseCommand):
    help = "Seed database with demo rooms and reservations"

    def handle(self, *args, **kwargs):

        # Create rooms
        rooms = []
        room_names = ["Pong", "Pac-Man", "Super Mario"]
        for name in room_names:
            room, _ = Room.objects.get_or_create(
                name=f"Sala {name}",
                defaults={"max_capacity": random.randint(4, 12)},
            )
            rooms.append(room)

        self.stdout.write(self.style.SUCCESS("Rooms created"))

        start_date = datetime(2026, 3, 1)
        end_date = datetime(2026, 3, 31)

        for _ in range(15):
            room = random.choice(rooms)

            random_day = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )

            start_hour = random.randint(8, 16)
            duration = random.choice([1, 2, 3])

            start_time = time(start_hour, 0)
            end_time = time(start_hour + duration, 0)

            Reservation.objects.create(
                room=room,
                date=random_day.date(),
                start_time=start_time,
                end_time=end_time,
                status=Reservation.Status.CONFIRMED,
            )

        self.stdout.write(self.style.SUCCESS("Reservations created"))
