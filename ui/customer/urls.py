"""
Django URL configuration for the UI app.
"""

from django.urls import path

from . import views

app_name = "ui"

urlpatterns = [
    path("customers/types/", views.customer_type_list, name="customer_type_list"),
    path(
        "customers/types/add/", views.customer_type_create, name="customer_type_create"
    ),
    path(
        "customers/types/<int:pk>/edit/",
        views.customer_type_update,
        name="customer_type_update",
    ),
    path(
        "customers/types/<int:pk>/delete/",
        views.customer_type_delete,
        name="customer_type_delete",
    ),
    path("customers/", views.customers_view, name="customers"),
    path("customers/add/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_update, name="customer_update"),
    path("customers/<int:pk>/delete/", views.customer_delete, name="customer_delete"),
    path(
        "customers/search_customer/",
        views.search_customers,
        name="search_customers",
    ),
]
