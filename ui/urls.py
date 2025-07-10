"""
Django URL configuration for the UI app.
"""

from django.urls import path

from . import views

app_name = "ui"

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("", views.home, name="home"),  # Page d'accueil
    # Gestion des réservations
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
    path(
        "reservations/search_customer/",
        views.search_customers,
        name="search_customers",
    ),
    path("reservations/search_assets/", views.search_assets, name="search_assets"),
    # Gestion des clients
    path("customers/", views.customers_view, name="customers"),
    path("customers/add/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/edit/", views.customer_update, name="customer_update"),
    path("customers/<int:pk>/delete/", views.customer_delete, name="customer_delete"),
    # Gestion du stock
    path("stock/", views.stock_view, name="stock"),
    # Gestion des catégories (admin uniquement)
    path("stock/categories/", views.category_list, name="category_list"),
    path("stock/categories/add/", views.category_create, name="category_create"),
    path(
        "stock/categories/<int:pk>/edit/", views.category_update, name="category_update"
    ),
    path(
        "stock/categories/<int:pk>/delete/",
        views.category_delete,
        name="category_delete",
    ),
    # Gestion des articles
    path("stock/items/add/", views.item_create, name="item_create"),
    path("stock/items/<int:pk>/edit/", views.item_update, name="item_update"),
    path("stock/items/<int:pk>/delete/", views.item_delete, name="item_delete"),
    path("stock/items/<int:pk>/", views.item_detail, name="item_detail"),
    # Gestion des événements de stock
    path("stock/events/add/", views.stock_event_create, name="stock_event_create"),
    path(
        "stock/events/add/<int:asset_id>/",
        views.stock_event_create,
        name="stock_event_create_for_asset",
    ),
]
