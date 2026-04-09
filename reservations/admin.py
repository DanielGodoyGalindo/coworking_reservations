from django.contrib import admin
from reservations.models import Reservation
from rooms.models import Room

# Register your models here.
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "date", "start_time", "end_time", "status")
    list_filter = ("room", "date", "status")
    search_fields = ("user__username", "room__name")
    
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)