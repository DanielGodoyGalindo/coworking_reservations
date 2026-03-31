from django.shortcuts import render
from rooms.models import Room
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def dashboard_page(request):
    return render(request, "dashboard.html")


@login_required
def dashboard2_view(request):
    rooms = Room.objects.all()
    return render(request, "dashboard2.html", {"rooms": rooms})
