from datetime import date, time, datetime
from reservations.services import monthly_occupancy_rate, occupancy_rate
from reservations.models import Reservation
from django.test import TestCase
from rooms.models import Room
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta

User = get_user_model()


class ReservationMetricsTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            name="Sala Pong",
            max_capacity=10,
        )
        self.url = "/api/reservations/"
        self.user = User.objects.create_user(
            username="test",
            password="1234",
        )
        self.date = timezone.localdate() + timedelta(days=1)

    def test_monthly_occupancy_simple(self):

        Reservation.objects.create(
            room=self.room,
            date=date(2026, 3, 10),
            start_time=time(9, 0),
            end_time=time(11, 0),
            status=Reservation.Status.CONFIRMED,
        )

        rate = monthly_occupancy_rate(self.room, 2026, 3)
        print("OCCUPANCY RATE:", rate)

        self.assertGreater(rate, 0)
        self.assertLess(rate, 1)

    def test_day_occupancy_rate(self):

        target_date = date(2026, 3, 10)

        Reservation.objects.create(
            room=self.room,
            user=self.user,
            date=target_date,
            start_time=time(8, 0),
            end_time=time(11, 0),
            status=Reservation.Status.CONFIRMED,
        )

        occupancy = occupancy_rate(self.room, target_date)
        print("OCCUPANCY DAY RATE:", occupancy)

        self.assertAlmostEqual(occupancy, 0.3, places=2)
