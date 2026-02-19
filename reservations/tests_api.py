import json
from datetime import date, time, timedelta
from django.test import TestCase
from reservations.services import get_available_slots, create_reservation
from rooms.models import Room
from reservations.models import Reservation
from django.contrib.auth import get_user_model
from django.utils import timezone

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
        self.date = timezone.localdate() + timedelta(days=1)

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

    def test_no_overlap_when_touching_end(self):

        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        overlapping = Reservation.objects.filter(
            room=self.room,
            date=self.date,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
            start_time__lt=time(11, 0),
            end_time__gt=time(10, 0),
        ).exists()

        self.assertFalse(overlapping)

    def test_overlap_partial_at_start(self):

        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        overlapping = Reservation.objects.filter(
            room=self.room,
            date=self.date,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
            start_time__lt=time(10, 30),
            end_time__gt=time(9, 30),
        ).exists()

        self.assertTrue(overlapping)

    def test_overlap_partial_at_end(self):

        # Existing reservation
        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        self.client.login(username="test", password="1234")

        payload = {
            "room_id": self.room.id,
            "date": str(self.date),
            "start_time": "09:30",
            "end_time": "10:30",
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_cancelled_reservation_does_not_block(self):

        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CANCELLED,
            user=self.user,
        )

        overlapping = Reservation.objects.filter(
            room=self.room,
            date=self.date,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
            start_time__lt=time(10, 30),
            end_time__gt=time(9, 30),
        ).exists()

        self.assertFalse(overlapping)

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
        
    def test_overlap_full_containment(self):

        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        self.client.login(username="test", password="1234")

        payload = {
            "room_id": self.room.id,
            "date": str(self.date),
            "start_time": "08:00",
            "end_time": "11:00",
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("booked", response.json()["error"])
        
    def test_overlap_exact_same_time(self):

        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        self.client.login(username="test", password="1234")

        payload = {
            "room_id": self.room.id,
            "date": str(self.date),
            "start_time": "09:00",
            "end_time": "10:00",
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("booked", response.json()["error"])

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

        start_time = time(9, 0)
        end_time = time(10, 00)

        reservation = Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=start_time,
            end_time=end_time,
            status=Reservation.Status.CONFIRMED,
            user=self.user,
        )

        # Login with user, (soft) delete created reservation, get 200
        self.client.login(username="test", password="1234")
        response = self.client.delete(f"/api/reservations/{reservation.id}/")
        self.assertEqual(response.status_code, 200)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_expired_pending_does_not_block_slot(self):
        Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time="09:00",
            end_time="10:00",
            status=Reservation.Status.PENDING,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        slots = get_available_slots(
            room=self.room,
            date=self.date,
        )

        self.assertIn(
            (time(9, 0), time(9, 30)),
            slots,
        )

        self.assertIn(
            (time(9, 30), time(10, 0)),
            slots,
        )

    def test_create_30minutes_reservation(self):
        self.client.login(username="test", password="1234")

        start_time = time(12, 0)
        end_time = time(12, 30)

        with self.assertRaises(ValueError) as context:
            create_reservation(
                room=self.room,
                date=self.date,
                start_time=start_time,
                end_time=end_time,
                user=self.user,
            )

        self.assertIn("Minimum reservation is 60 minutes", str(context.exception))

    def test_confirm_own_pending_reservation_success(self):

        reservation = Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.PENDING,
            user=self.user,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        self.client.login(username="test", password="1234")
        response = self.client.post(f"/api/reservations/{reservation.id}/confirm/")
        self.assertEqual(response.status_code, 200)

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)
        self.assertIsNone(reservation.expires_at)

    def test_confirm_other_user_reservation_returns_403(self):

        User = get_user_model()

        reservation_user = User.objects.create_user(
            username="user",
            password="1234",
        )

        other_user = User.objects.create_user(
            username="other",
            password="1234",
        )

        reservation = Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.PENDING,
            user=reservation_user,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        self.client.login(username="other", password="1234")
        response = self.client.post(f"/api/reservations/{reservation.id}/confirm/")
        self.assertEqual(response.status_code, 403)

    def test_confirm_expired_reservation_returns_400(self):

        expired_reservation = Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.PENDING,
            user=self.user,
            expires_at=timezone.now() - timedelta(minutes=10),
        )

        self.client.login(username="test", password="1234")
        response = self.client.post(
            f"/api/reservations/{expired_reservation.id}/confirm/"
        )
        self.assertEqual(response.status_code, 400)
        expired_reservation.refresh_from_db()
        self.assertEqual(expired_reservation.status, Reservation.Status.CANCELLED)
        self.assertIn("expired", response.json()["error"])

    def test_confirm_already_confirmed_returns_400(self):

        confirmed_reservation = Reservation.objects.create(
            room=self.room,
            date=self.date,
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=Reservation.Status.CONFIRMED,
            user=self.user,
            expires_at=None,
        )

        self.client.login(username="test", password="1234")
        response = self.client.post(
            f"/api/reservations/{confirmed_reservation.id}/confirm/"
        )
        self.assertEqual(response.status_code, 400)
        confirmed_reservation.refresh_from_db()
        self.assertEqual(confirmed_reservation.status, Reservation.Status.CONFIRMED)
