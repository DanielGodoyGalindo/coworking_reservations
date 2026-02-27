from django.core.management.base import BaseCommand
from reservations.services.reservations import expire_pending_reservations

# Custom Django Management Commands
# https://testdriven.io/tips/dbc14e1f-1231-4761-8ed4-3c82f8b16c08/


class Command(BaseCommand):
    help = "Expire pending reservations"

    def handle(self, *args, **kwargs):
        count = expire_pending_reservations()
        self.stdout.write(f"Expired {count} reservations")