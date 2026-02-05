from django.test import TestCase
import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError
from rooms.models import Room
from reservations.models import Reservation
from reservations.services import create_reservation

# Create your tests here.

User = get_user_model()


class ReservationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
        )

        self.room = Room.objects.create(
            name="Sala Space Invaders",
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
            name="Sala Space Invaders",
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

    # Not allowed with new reservation 10:00-12:00h
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

    # Not allowed reservation
    def test_cannot_create_reservation_with_exact_same_time(self):
        with self.assertRaises(ValidationError):
            create_reservation(
                user=self.user,
                room=self.room,
                date=datetime.date(2026, 1, 10),
                start_time=datetime.time(9, 0),
                end_time=datetime.time(11, 0),
            )

    # Existing reservation 09:00–13:00 and new reservation 10:00-11:00h
    def test_cannot_create_reservation_inside_existing_one(self):
        self.existing_reservation.start_time = datetime.time(9, 0)
        self.existing_reservation.end_time = datetime.time(13, 0)
        self.existing_reservation.save()
        with self.assertRaises(ValidationError):
            create_reservation(
                user=self.user,
                room=self.room,
                date=datetime.date(2026, 1, 10),
                start_time=datetime.time(10, 0),
                end_time=datetime.time(11, 0),
            )

    # Existing 10-11h and new 9-13h
    def test_cannot_create_reservation_wrapping_existing_one(self):
        self.existing_reservation.start_time = datetime.time(10, 0)
        self.existing_reservation.end_time = datetime.time(11, 0)
        self.existing_reservation.save()
        with self.assertRaises(ValidationError):
            create_reservation(
                user=self.user,
                room=self.room,
                date=datetime.date(2026, 1, 10),
                start_time=datetime.time(9, 0),
                end_time=datetime.time(13, 0),
            )

    # Allowed reservation
    def test_same_time_different_room_is_allowed(self):
        other_room = Room.objects.create(
            name="Sala Pong",
            max_capacity=8,
        )
        reservation = create_reservation(
            user=self.user,
            room=other_room,
            date=datetime.date(2026, 1, 10),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(11, 0),
        )
        self.assertIsNotNone(reservation.id)

    # Time not allowed
    def test_cannot_create_reservation_with_invalid_time_range(self):
        with self.assertRaises(ValidationError):
            create_reservation(
                user=self.user,
                room=self.room,
                date=datetime.date(2026, 1, 10),
                start_time=datetime.time(11, 0),
                end_time=datetime.time(9, 0),
            )
