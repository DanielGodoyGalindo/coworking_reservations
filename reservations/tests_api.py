import json
from datetime import date
from django.test import TestCase
from rooms.models import Room
from reservations.models import Reservation
from django.contrib.auth import get_user_model

User = get_user_model()


class ReservationAPITest(TestCase):
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

    def test_create_reservation_success(self):
        payload = {
            "room_id": self.room.id,
            "date": "2026-02-10",
            "start_time": "09:00",
            "end_time": "10:00",
        }

        # Login before POST
        self.client.login(username="test", password="1234")

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
            user=self.user,
        )

        payload = {
            "room_id": self.room.id,
            "date": "2026-02-10",
            "start_time": "09:30",
            "end_time": "10:30",
        }

        # Login before POST
        self.client.login(username="test", password="1234")

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

        self.client.login(username="test", password="1234")

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        payload = {
            "room_id": self.room.id,
            "date": "2026-02-10",
            "start_time": "09:00",
            "end_time": "10:00",
        }

        # No login before POST
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_list_reservations_unauthenticated_returns_401(self):
        response = self.client.get("/api/my-reservations/")
        self.assertEqual(response.status_code, 401)

    def test_list_reservations_authenticated_returns_200(self):
        self.client.login(username="test", password="1234")
        response = self.client.get("/api/my-reservations/")
        self.assertEqual(response.status_code, 200)

    def test_list_returns_only_user_reservations(self):

        from django.contrib.auth import get_user_model

        # Create other user
        User = get_user_model()
        other_user = User.objects.create_user(
            username="other",
            password="1234",
        )

        # Create reservation with current user
        Reservation.objects.create(
            room=self.room,
            date=date(2026, 2, 10),
            start_time="09:00",
            end_time="10:00",
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        # Create reservation with other user
        Reservation.objects.create(
            room=self.room,
            date=date(2026, 2, 11),
            start_time="11:00",
            end_time="12:00",
            status=Reservation.Status.CONFIRMED,
            user=other_user,
        )

        self.client.login(username="test", password="1234")
        response = self.client.get("/api/my-reservations/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["reservations"]), 1)
        self.assertEqual(data["reservations"][0]["date"], "2026-02-10")

    def test_delete_unauthenticated_returns_401(self):

        # Create reservation
        reservation = Reservation.objects.create(
            room=self.room,
            date=date(2026, 2, 10),
            start_time="09:00",
            end_time="10:00",
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        # Try to delete without authentication
        response = self.client.delete(f"/api/reservations/{reservation.id}/")
        self.assertEqual(response.status_code, 401)

    def test_delete_other_user_reservation_returns_403(self):

        User = get_user_model()
        other_user = User.objects.create_user(
            username="other",
            password="1234",
        )

        reservation = Reservation.objects.create(
            room=self.room,
            date=date(2026, 2, 10),
            start_time="09:00",
            end_time="10:00",
            status=Reservation.Status.CONFIRMED,
            user=other_user,
        )

        # Login with current user, try to delete created reservation then get 403
        self.client.login(username="test", password="1234")
        response = self.client.delete(f"/api/reservations/{reservation.id}/")
        self.assertEqual(response.status_code, 403)
        
    def test_delete_own_reservation_success(self):

        reservation = Reservation.objects.create(
            room=self.room,
            date=date(2026, 2, 10),
            start_time="09:00",
            end_time="10:00",
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        # Login with user, delete created reservation, get 200
        self.client.login(username="test", password="1234")
        response = self.client.delete(f"/api/reservations/{reservation.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 0)
