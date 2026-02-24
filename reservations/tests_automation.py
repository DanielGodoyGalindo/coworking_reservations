from datetime import date, time, datetime
from reservations.services import (
    expire_pending_reservations,
    monthly_occupancy_rate,
    occupancy_rate,
)
from reservations.models import Reservation
from django.test import TestCase
from rooms.models import Room
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta

User = get_user_model()


class ReservationAutomationTest(TestCase):
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


def test_expire_pending_reservations(self):
    expired_reservation = Reservation.objects.create(
        room=self.room,
        date=self.date,
        start_time=time(9, 0),
        end_time=time(10, 0),
        status=Reservation.Status.PENDING,
        expires_at=timezone.now() - timedelta(minutes=5),
    )

    count = expire_pending_reservations()

    expired_reservation.refresh_from_db()

    self.assertEqual(count, 1)
    self.assertEqual(expired_reservation.status, Reservation.Status.CANCELLED)
