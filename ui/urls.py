"""
Django URL configuration for the UI app.
"""

from django.urls import path

from . import views
from .customer.urls import urlpatterns as customer_urls
from .reservation.urls import urlpatterns as reservation_urls
from .stock.urls import urlpatterns as stock_urls

app_name = "ui"

urlpatterns = (
    [
        path("health/", views.health_check, name="health_check"),
        path("", views.home, name="home"),  # Page d'accueil
    ]
    + reservation_urls
    + customer_urls
    + stock_urls
)
