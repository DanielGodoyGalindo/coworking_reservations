import json
from datetime import date
from django.test import TestCase
from rooms.models import Room
from reservations.models import Reservation


class ReservationAPITest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            name="Pong",
            max_capacity=10,
        )
        self.url = "/api/reservations/"

    def test_create_reservation_success(self):
        payload = {
            "room_id": self.room.id,
            "date": "2026-02-10",
            "start_time": "09:00",
            "end_time": "10:00",
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_create_reservation_overlap_returns_409(self):
        Reservation.objects.create(
            room=self.room,
            date=date(2026, 2, 10),
            start_time="09:00",
            end_time="10:00",
            status=Reservation.Status.CONFIRMED,
        )

        payload = {
            "room_id": self.room.id,
            "date": "2026-02-10",
            "start_time": "09:30",
            "end_time": "10:30",
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_missing_fields_returns_400(self):
        payload = {
            "room_id": self.room.id,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
