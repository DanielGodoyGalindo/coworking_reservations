from django.db import models
from django.conf import settings


# Create your models here.
class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
        null=True,
        blank=True,
    )
    room = models.ForeignKey(
        "rooms.Room",
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    @staticmethod
    def overlapping_exists(room, date, start_time, end_time):
        return Reservation.objects.filter(
            room=room,
            date=date,
            status__in=[
                Reservation.Status.PENDING,
                Reservation.Status.CONFIRMED,
            ],
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()

    class Meta:
        indexes = [
            models.Index(fields=["room", "date"]),
        ]
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.room} | {self.date} {self.start_time}-{self.end_time}"
