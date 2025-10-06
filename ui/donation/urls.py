"""
URLs for the donation app.
"""

from django.urls import path

from ui.donation import views

urlpatterns = [
    path("donations/", views.donation_list, name="donation_list"),
    path("donations/create/", views.donation_create, name="donation_create"),
    path("donations/<int:pk>/edit/", views.donation_update, name="donation_update"),
    path("donations/<int:pk>/delete/", views.donation_delete, name="donation_delete"),
]
