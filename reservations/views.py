from django.shortcuts import render

# Create your views here.
def dashboard_page(request):
    return render(request, "dashboard.html")

def dashboard2_view(request):
    return render(request, "dashboard2.html")