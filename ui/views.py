"""
views.py

defines the views for the UI application, including a health check endpoint.
"""

from django.http import HttpResponse

from accounts.decorators import get_capability


def health_check(request):
    return HttpResponse("OK", status=200)


# views.py
from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .stock.models import StockEvent
from .reservation.models import Reservation
from .donation.models import Donation


def get_next_collection_day():
    """
    Retourne le prochain jour de collecte (lundi ou vendredi).
    - Vendredi si on est entre lundi 19h et vendredi 19h
    - Lundi sinon
    """
    now = timezone.now()
    current_weekday = now.weekday()  # 0=Lundi, 4=Vendredi
    current_hour = now.hour

    # Si on est entre lundi 19h et vendredi 19h -> prochain vendredi
    if (
        (current_weekday == 0 and current_hour >= 19)
        or (0 < current_weekday < 4)
        or (current_weekday == 4 and current_hour < 19)
    ):
        target_day = 4  # Vendredi
        day_name = "Vendredi"
    else:
        # Sinon -> prochain lundi
        target_day = 0  # Lundi
        day_name = "Lundi"

    today = now.date()
    days_ahead = target_day - current_weekday
    if days_ahead <= 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead), day_name


def home(request):
    # Articles en panne
    articles_endommages = (
        StockEvent.objects.filter(event_type=StockEvent.EventType.REPAIRABLE_ISSUE)
        .values("asset")
        .distinct()
        .count()
    )

    # Réservations de l'année
    annee_actuelle = timezone.now().year
    reservations_closes = Reservation.objects.filter(
        actual_return_date__year=annee_actuelle, status="returned"
    ).count()

    reservations_en_cours = Reservation.objects.filter(status="checked_out").count()

    # Prochain jour de collecte
    prochain_jour, nom_jour = get_next_collection_day()

    # Retours du prochain jour
    retours = Reservation.objects.filter(
        return_date__date=prochain_jour, status="checked_out"
    ).select_related("customer", "customer__customer_type")

    # Départs du prochain jour
    departs = Reservation.objects.filter(
        checkout_date__date=prochain_jour, status="validated"
    ).select_related("customer", "customer__customer_type")

    # Dons reçus cette année
    dons_annee = (
        Donation.objects.filter(date__year=annee_actuelle).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    context = {
        "articles_endommages": articles_endommages,
        "reservations_closes": reservations_closes,
        "reservations_en_cours": reservations_en_cours,
        "nb_retours": retours.count(),
        "nb_departs": departs.count(),
        "dons_annee": dons_annee,
        "prochain_jour": prochain_jour,
        "nom_jour": nom_jour,
        "retours": retours,
        "departs": departs,
        "capability": get_capability(request.user),
    }

    return render(request, "ui/home.html", context)
