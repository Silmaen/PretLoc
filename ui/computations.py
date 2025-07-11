"""
Calculations related to asset status and reservations.
"""

from django.db.models import Q
from django.utils import timezone

from .models import StockEvent, ReservationItem


def get_asset_status_at_date(asset, date=None):
    """
    Calcule les quantités d'un article en tenant compte de l'historique complet
    des réservations et événements de stock à une date donnée.

    Args:
        asset: L'article (Asset)
        date: La date pour laquelle calculer l'état (par défaut: maintenant)

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
    damaged_from_events = 0

    for event in stock_events:
        if event.event_type in ["SALE", "DESTRUCTION"]:
            total_stock -= event.quantity
        elif event.event_type in ["ACQUISITION", "INVENTORY_ADJUSTMENT"]:
            total_stock += event.quantity
        elif event.event_type == "ISSUE":
            damaged_from_events += event.quantity
        elif event.event_type == "REPAIR":
            damaged_from_events -= event.quantity

    # 2. Articles en sortie active à la date spécifiée
    checked_out_items = ReservationItem.objects.filter(
        Q(reservation__status="checked_out")
        | Q(reservation__status="returned", reservation__actual_return_date__gt=date),
        asset=asset,
        reservation__actual_checkout_date__lte=date,
    )

    checked_out_count = sum(item.quantity_checked_out for item in checked_out_items)

    # 3. Articles endommagés suite aux retours
    damaged_returns = ReservationItem.objects.filter(
        asset=asset,
        reservation__status="returned",
        quantity_damaged__gt=0,
        reservation__actual_return_date__lte=date,
    )

    damaged_from_returns = sum(item.quantity_damaged for item in damaged_returns)
    damaged_count = damaged_from_events + damaged_from_returns
    if damaged_count < 0:
        damaged_count = 0

    # 4. Articles réservés mais pas encore sortis
    reserved_items = ReservationItem.objects.filter(
        Q(reservation__actual_checkout_date__isnull=True)
        | Q(reservation__actual_checkout_date__gt=date),
        asset=asset,
        reservation__status__in=["created", "validated"],
        reservation__checkout_date__lte=date,
    )

    reserved_count = sum(item.quantity_reserved for item in reserved_items)

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
