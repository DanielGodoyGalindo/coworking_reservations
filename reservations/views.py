from django.shortcuts import render
from rooms.models import Room
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


# Create your views here.
@login_required
def dashboard_page(request):
    return render(request, "dashboard.html")


@login_required
def dashboard2_view(request):
    rooms = Room.objects.all()
    return render(request, "dashboard2.html", {"rooms": rooms})

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
