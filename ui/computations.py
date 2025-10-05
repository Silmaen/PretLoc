"""
Calculations related to asset status and reservations.
"""

import logging

from django.db.models import Q
from django.utils import timezone

from ui.reservation.models import ReservationItem
from ui.stock.models import StockEvent

logger = logging.getLogger(__name__)


def get_asset_status_at_date(asset, date=None, excluded_reservation=None):
    """
    Compute amounts of an asset considering the full history
    of reservations and stock events at a given date.

    :param asset: The asset (Asset)
    :param date: Date for which to compute the status (defaults to now if None)
    :param excluded_reservation: Reservation to exclude from calculations (optional)

    :return:
        dict: Status at the given date:
            - damaged: number of damaged items
            - checked_out: number of checked out items
            - reserved: number of reserved items
            - available: number of available items
            - total: total stock
    """

    if date is None:
        date = timezone.now()

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

    # for each reservation, determine its status at the given date
    for reservation in reservations:
        reserved_count += reservation.quantity_reserved

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
    Analyze the availability of an asset over a given period.
    Calculate critical values: minimum stock, maximum damaged products,
    maximum checked out or reserved products, and minimum available products.

    :param asset: The asset (Asset)
    :param start_date: Start date of the period
    :param end_date: End date of the period (end date is exclusive).
    :param excluded_reservation: Reservation to exclude from calculations (optional)

    :return:
        dict: Analysis results:
            - total: stock total at the worst moment
            - damaged: nombre maximum en panne
            - reserved: nombre maximum réservé
            - available: nombre minimum disponible
    """
    if start_date > end_date:
        raise {
            "total": 0,
            "damaged": 0,
            "reserved": 0,
            "available": 0,
        }

    critical_dates = {start_date, end_date}

    stock_events = StockEvent.objects.filter(
        asset=asset, date__gte=start_date, date__lte=end_date
    ).order_by("date")

    for event in stock_events:
        critical_dates.add(event.date)

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
        if start_date <= item.reservation.get_start_date() <= end_date:
            critical_dates.add(item.reservation.get_start_date())
        if start_date <= item.reservation.get_return_date() <= end_date:
            critical_dates.add(item.reservation.get_return_date())

    min_total = float("inf")
    max_damaged = 0
    max_reserved = 0
    min_available = float("inf")

    critical_dates = sorted(list(critical_dates))

    for date in critical_dates:
        status = get_asset_status_at_date(asset, date, excluded_reservation)
        min_total = min(min_total, status["total"])
        max_damaged = max(max_damaged, status["damaged"])
        max_reserved = max(max_reserved, status["reserved"])
        min_available = min(min_available, status["available"])

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
    Verify the availability of items for a given reservation.
    :parm reservation: The reservation to check (Reservation)
    :return:
        dict: Check results:
            - is_ok: True if all items are available in the requested quantities
            - problematic_items: dict of items with insufficient availability
    """
    problematic_items = {}
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
