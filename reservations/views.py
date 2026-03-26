from django.shortcuts import render

from rooms.models import Room


# Create your views here.
def dashboard_page(request):
    return render(request, "dashboard.html")


def dashboard2_view(request):
    rooms = Room.objects.all()
    return render(request, "dashboard2.html", {"rooms": rooms})
