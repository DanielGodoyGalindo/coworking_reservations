from datetime import datetime
from django.test import TestCase
from reservations.models import Reservation
from reservations.tests.tests import User
from rooms.models import Room


class AvailabilityTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="password",
        )

        self.room = Room.objects.create(
            name="Sala Pac-Man",
            max_capacity=10,
        )

    def test_full_day_available_when_no_reservations(self):
        slots = get_available_slots(
            room=self.room,
            date=datetime.date(2026, 1, 10),
        )

        self.assertEqual(
            slots,
            [
                (datetime.time(8, 0), datetime.time(18, 0)),
            ]
        )
        
    def test_availability_with_one_reservation(self):
        Reservation.objects.create(
            user=self.user,
            room=self.room,
            date=datetime.date(2026, 1, 10),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(12, 0),
        )

        slots = get_available_slots(
            room=self.room,
            date=datetime.date(2026, 1, 10),
        )

        self.assertEqual(
            slots,
            [
                (datetime.time(8, 0), datetime.time(10, 0)),
                (datetime.time(12, 0), datetime.time(18, 0)),
            ]
        )
        
    def test_availability_with_multiple_reservations(self):
        Reservation.objects.create(
            user=self.user,
            room=self.room,
            date=datetime.date(2026, 1, 10),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )

        Reservation.objects.create(
            user=self.user,
            room=self.room,
            date=datetime.date(2026, 1, 10),
            start_time=datetime.time(13, 0),
            end_time=datetime.time(14, 0),
        )

        slots = get_available_slots(
            room=self.room,
            date=datetime.date(2026, 1, 10),
        )

        self.assertEqual(
            slots,
            [
                (datetime.time(8, 0), datetime.time(9, 0)),
                (datetime.time(10, 0), datetime.time(13, 0)),
                (datetime.time(14, 0), datetime.time(18, 0)),
            ]
        )