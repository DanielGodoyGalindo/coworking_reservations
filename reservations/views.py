from django.shortcuts import render

# Create your views here.
def dashboard_page(request):
    return render(request, "dashboard.html")