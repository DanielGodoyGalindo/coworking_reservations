"""
URL configuration for coworking_reservations project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from reservations.views import create_reservation_html_view, dashboard2_view, dashboard_page, my_reservation_info_view, my_reservations_view
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login'), name='root'),
    path("admin/", admin.site.urls, name="admin"),
    path("api/", include("reservations.api.urls")),
    path("dashboard/", dashboard_page, name="dashboard"),
    path("dashboard2/", dashboard2_view, name="dashboard2"),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("create/", create_reservation_html_view, name="create_reservation"),
    path("my-reservations/", my_reservations_view, name="my_reservations"),
    path("my-reservations/<int:reservation_id>/", my_reservation_info_view),
]