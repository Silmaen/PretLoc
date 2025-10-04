"""
Django URL configuration for the UI app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("stock/", views.stock_view, name="stock"),
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
    path("stock/items/add/", views.item_create, name="item_create"),
    path("stock/items/<int:pk>/edit/", views.item_update, name="item_update"),
    path("stock/items/<int:pk>/delete/", views.item_delete, name="item_delete"),
    path("stock/items/<int:pk>/", views.item_detail, name="item_detail"),
    path("stock/events/add/", views.stock_event_create, name="stock_event_create"),
    path(
        "stock/events/add/<int:asset_id>/",
        views.stock_event_create,
        name="stock_event_create_for_asset",
    ),
]
