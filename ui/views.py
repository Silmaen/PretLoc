"""
views.py

defines the views for the UI application, including a health check endpoint.
"""

from django.http import HttpResponse
from django.shortcuts import redirect


def health_check(request):
    return HttpResponse("OK", status=200)


def home(request):
    return redirect("ui:reservations")
    # return render(request, "ui/home.html", {"capability": get_capability(request.user)})
