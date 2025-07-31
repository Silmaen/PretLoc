"""
Calculations related to asset status and reservations.
"""

import logging

from django.db.models import Q
from django.utils import timezone

from .models import StockEvent, ReservationItem

logger = logging.getLogger(__name__)


def get_asset_status_at_date(asset, date=None, excluded_reservation=None):
    """
    Calcule les quantités d'un article en tenant compte de l'historique complet
    des réservations et événements de stock à une date donnée.

    Args:
        asset: L'article (Asset)
        date: La date pour laquelle calculer l'état (par défaut: maintenant)
        excluded_reservation: Réservation à exclure des calculs (optionnel)

    Returns:
        dict: État de l'article avec les quantités:
            - damaged: nombre en panne
            - checked_out: nombre sorti en prêt
            - reserved: nombre réservé mais pas encore sorti
            - available: nombre disponible
            - total: stock total à cette date
    """

    if date is None:
        date = timezone.now()

    # 1. Calculer le stock total à la date spécifiée via les événements de stock
    stock_events = StockEvent.objects.filter(asset=asset, date__lte=date).order_by(
        "date"
    )

    total_stock = asset.stock_quantity
    damaged_count = 0
    reserved_count = 0
    checked_out_count = 0

    for event in stock_events:
        if event.event_type in ["SALE", "DESTRUCTION"]:
            total_stock -= event.quantity
        elif event.event_type in ["ACQUISITION", "INVENTORY_ADJUSTMENT"]:
            total_stock += event.quantity
        elif event.event_type == "ISSUE":
            damaged_count += event.quantity
        elif event.event_type == "REPAIR":
            damaged_count -= event.quantity

    # reservation that concerns the asset
    reservations = ReservationItem.objects.filter(asset=asset).exclude(
        reservation__status__in=["cancelled", "returned"]
    )
    if excluded_reservation:
        reservations = reservations.exclude(reservation__pk=excluded_reservation.pk)
    # exclude the reservation if start after the date or end before the date
    reservations = [
        reservation
        for reservation in reservations
        if (
            reservation.reservation.get_start_date()
            <= date
            <= reservation.reservation.get_return_date()
        )
    ]
    logger.debug(f"reservations for asset {asset.pk} at {date}: {reservations}")

    # for each reservation, determine its status at the given date
    for reservation in reservations:
        reserved_count += reservation.quantity_reserved

    # 5. Calculer les disponibles
    available_count = max(
        0, total_stock - (damaged_count + checked_out_count + reserved_count)
    )

    return {
        "damaged": damaged_count,
        "checked_out": checked_out_count,
        "reserved": reserved_count,
        "available": available_count,
        "total": total_stock,
    }


def analyze_asset_availability(asset, start_date, end_date, excluded_reservation=None):
    """
    Analyse la disponibilité d'un article sur une période donnée.
    Calcule les valeurs critiques: stock minimal, maximum de produits endommagés,
    maximum de produits sortis ou réservés et minimum de produits disponibles.

    Args:
        asset: L'article (Asset)
        start_date: Date de début de la période
        end_date: Date de fin de la période (doit être postérieure à start_date)
        excluded_reservation: Réservation à exclure des calculs (optionnel)

    Returns:
        dict: Valeurs critiques sur la période:
            - min_total: stock total minimum
            - max_damaged: nombre maximum en panne
            - max_reserved: nombre maximum réservé
            - min_available: nombre minimum disponible
    """
    # Validation des dates
    if start_date > end_date:
        raise {
            "total": 0,
            "damaged": 0,
            "reserved": 0,
            "available": 0,
        }

    # 1. Collecter toutes les dates critiques (points de changement potentiels)
    critical_dates = {start_date, end_date}

    # Ajouter les dates des événements de stock
    stock_events = StockEvent.objects.filter(
        asset=asset, date__gte=start_date, date__lte=end_date
    ).order_by("date")

    for event in stock_events:
        critical_dates.add(event.date)

    # Ajouter les dates de début et fin des réservations qui intersectent la période
    reservations = asset.reservation_items.filter(
        ~Q(reservation__status__in=["returned", "cancelled"])
    ).select_related("reservation")

    if excluded_reservation:
        reservations = reservations.exclude(reservation=excluded_reservation)
    reservations = [
        item
        for item in reservations
        if (
            start_date < item.reservation.get_return_date() < end_date
            or start_date < item.reservation.get_start_date() < end_date
        )
    ]

    for item in reservations:
        logger.debug(
            f"Potential critical res: {item.reservation.pk} ({item.reservation.customer} - {item.reservation.status}): "
        )
        if start_date <= item.reservation.get_start_date() <= end_date:
            critical_dates.add(item.reservation.get_start_date())
        if start_date <= item.reservation.get_return_date() <= end_date:
            critical_dates.add(item.reservation.get_return_date())

    # 2. Calculer l'état à chaque date critique et garder les valeurs extrêmes
    min_total = float("inf")
    max_damaged = 0
    max_reserved = 0
    min_available = float("inf")

    # Ordonner les dates
    critical_dates = sorted(list(critical_dates))

    for date in critical_dates:
        status = get_asset_status_at_date(asset, date, excluded_reservation)
        logger.debug(f"availability at {date}: {status}")
        # Mettre à jour les valeurs extrêmes
        min_total = min(min_total, status["total"])
        max_damaged = max(max_damaged, status["damaged"])
        max_reserved = max(max_reserved, status["reserved"])
        min_available = min(min_available, status["available"])

    # Si aucune donnée n'a été trouvée, min_total sera toujours à l'infini
    if min_total == float("inf"):
        min_total = 0
    if min_available == float("inf"):
        min_available = 0

    return {
        "total": min_total,
        "damaged": max_damaged,
        "reserved": max_reserved,
        "available": min_available,
    }


def check_reservation_availability(reservation):
    """
    Vérifie la disponibilité des articles pour une réservation donnée.

    Args:
        reservation: Instance de la réservation (Reservation)

    Returns:
        dict: Résultat de la vérification:
            - is_ok: booléen indiquant si la réservation est valide
            - problematic_items: liste des articles problématiques
    """
    problematic_items = {}

    logger.debug(
        f"Checking availability for reservation {reservation.pk} ({reservation.customer} sortie: {reservation.get_start_date()})"
    )
    real_start = reservation.get_start_date()
    real_end = reservation.get_return_date()

    for item in reservation.items.all():
        availability = analyze_asset_availability(
            asset=item.asset,
            start_date=real_start,
            end_date=real_end,
            excluded_reservation=reservation,
        )
        if item.quantity_reserved > availability["available"]:
            problematic_items[item.asset.name] = {
                "reserved_quantity": item.quantity_reserved,
                "available_quantity": availability["available"],
            }

    return {
        "is_ok": len(problematic_items) == 0,
        "problematic_items": problematic_items,
    }
