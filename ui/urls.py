"""
Django URL configuration for the UI app.
"""

from django.urls import path

from . import views

app_name = "ui"

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("", views.home, name="home"),  # Page d'accueil
    path(
        "reservations/", views.home, name="reservations"
    ),  # Dummy path for reservations
    path("stock/", views.home, name="stock"),  # Dummy page for stock management
]
