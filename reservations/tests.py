from django.test import TestCase

# Create your tests here.
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

from rooms.models import Room
from reservations.models import Reservation
from reservations.services import create_reservation


User = get_user_model()


class ReservationModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
        )

        self.room = Room.objects.create(
            name="Sala Norte",
            max_capacity=10,
        )

    def test_can_create_reservation(self):
        reservation = Reservation.objects.create(
            user=self.user,
            room=self.room,
            date=datetime.date(2026, 1, 10),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(11, 0),
        )

        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.room, self.room)
        self.assertEqual(reservation.status, Reservation.Status.PENDING)


class ReservationOverlapTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="password",
        )

        self.room = Room.objects.create(
            name="Sala Norte",
            max_capacity=10,
        )

        # Existing reservation with time: 09:00h - 11:00h
        self.existing_reservation = Reservation.objects.create(
            user=self.user,
            room=self.room,
            date=datetime.date(2026, 1, 10),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(11, 0),
        )

    def test_cannot_create_overlapping_reservation(self):
        """
        New reservation overlaps: 10:00 - 12:00
        """
        with self.assertRaises(ValidationError):
            create_reservation(
                user=self.user,
                room=self.room,
                date=datetime.date(2026, 1, 10),
                start_time=datetime.time(10, 0),
                end_time=datetime.time(12, 0),
            )