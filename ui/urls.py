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
    path("customers/", views.home, name="customers"),  # Dummy path for reservations
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
]
