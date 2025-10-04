"""
Django URL configuration for the UI app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("reservations/", views.reservation_list, name="reservations"),
    path("reservations/add/", views.reservation_create, name="reservation_create"),
    path("reservations/<int:pk>/", views.reservation_detail, name="reservation_detail"),
    path(
        "reservations/<int:pk>/validate/",
        views.reservation_validate,
        name="reservation_validate",
    ),
    path(
        "reservations/<int:pk>/edit/",
        views.reservation_update,
        name="reservation_update",
    ),
    path(
        "reservations/<int:pk>/cancel/",
        views.reservation_cancel,
        name="reservation_cancel",
    ),
    path(
        "reservations/<int:pk>/checkout/",
        views.reservation_checkout,
        name="reservation_checkout",
    ),
    path(
        "reservations/<int:pk>/return/",
        views.reservation_return,
        name="reservation_return",
    ),
    path("reservations/search_assets/", views.search_assets, name="search_assets"),
    path("reservations/check/", views.check_reservation, name="check_reservation"),
    path("reservations/<int:pk>/pdf/", views.reservation_pdf, name="reservation_pdf"),
    path(
        "reservations/calendar_data/",
        views.reservation_calendar_data,
        name="reservation_calendar_data",
    ),
]
