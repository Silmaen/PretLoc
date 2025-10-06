"""
Views for managing reservations.
"""

import base64
import datetime
from io import BytesIO
from pathlib import Path

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import IntegerField, Value, Q
from django.db.models.expressions import Case, When
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML

from accounts.decorators import user_type_required, get_capability
from ui.donation.models import Donation
from ui.stock.models import Category
from utils.computations import (
    check_reservation_availability,
    analyze_asset_availability,
    get_asset_status_at_date,
)
from utils.period import Period
from .forms import (
    ReservationForm,
    ReservationItemForm,
)
from .models import (
    Asset,
    Reservation,
    ReservationItem,
)


@login_required
@user_type_required("manager")
def reservation_list(request):
    """
    Display a list of reservations with filtering, searching, and sorting capabilities.
    :param request: HTTP request object
    :return: Rendered reservation list page
    """
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    sort = request.GET.get("sort", "checkout_date")
    direction = request.GET.get("direction", "desc")
    active_only = request.GET.get("active_only", "false")

    order_by = sort

    if sort == "status":
        status_order = {
            "created": 1,
            "validated": 2,
            "checked_out": 3,
            "returned": 4,
            "cancelled": 5,
        }

        status_ordering = Case(
            *[When(status=k, then=Value(v)) for k, v in status_order.items()],
            output_field=IntegerField(),
        )

        if direction == "desc":
            status_ordering = status_ordering.desc()

        reservations_query = Reservation.objects.annotate(status_order=status_ordering)
        order_by = "status_order"
    else:
        reservations_query = Reservation.objects.all()
        if direction == "desc" and sort != "status":
            order_by = f"-{order_by}"

    filters = {}

    if status_filter:
        filters["status"] = status_filter

    if active_only == "true":
        if "status" in filters:
            if filters["status"] not in ["returned", "cancelled"]:
                pass
            else:
                active_only = "false"
        else:
            filters["status__in"] = ["created", "validated", "checked_out"]

    if search_query:
        reservations = reservations_query.filter(
            Q(customer__last_name__icontains=search_query)
            | Q(customer__first_name__icontains=search_query)
            | Q(customer__company_name__icontains=search_query)
            | Q(customer__email__icontains=search_query)
            | Q(notes__icontains=search_query),
            **filters,
        ).order_by(order_by)
    else:
        reservations = reservations_query.filter(**filters).order_by(order_by)

    for reservation in reservations:
        if reservation.status in ["created", "validated"]:
            # Calculer la disponibilité des articles pour les réservations en cours
            check_result = check_reservation_availability(reservation)
            reservation.is_ok = check_result["is_ok"]
        else:
            reservation.is_ok = True

    context = {
        "reservations": reservations,
        "search_query": search_query,
        "status_filter": status_filter,
        "sort": sort,
        "direction": direction,
        "active_only": active_only,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/list.html", context)


@login_required
@user_type_required("manager")
def reservation_detail(request, pk):
    """
    Display detailed information about a specific reservation.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to display
    :return: Rendered reservation detail page
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    items = reservation.items.all().order_by("asset__category__name", "asset__name")

    if reservation.status in ["created", "validated"]:
        check_result = check_reservation_availability(reservation)
        reservation.is_ok = check_result["is_ok"]
        for item in items:
            if item.asset.name in check_result["problematic_items"].keys():
                item.is_problematic = True
                item.available = check_result["problematic_items"][item.asset.name][
                    "available_quantity"
                ]
            else:
                item.is_problematic = False

    customer_membership = reservation.customer.get_has_paid_membership_fee(
        reservation.true_return_date.year
    )
    customer_membership_fee = reservation.customer.get_membership_fee(
        reservation.true_return_date.year
    )

    context = {
        "reservation": reservation,
        "items": items,
        "capability": get_capability(request.user),
        "customer_membership": customer_membership,
        "customer_membership_fee": customer_membership_fee,
    }
    return render(request, "ui/reservations/detail.html", context)


@login_required
@user_type_required("manager")
def reservation_create(request):
    """
    Create a new reservation.
    :param request: HTTP request object
    :return: Rendered reservation creation form or redirect on success
    """
    ReservationItemFormSet = inlineformset_factory(
        Reservation, ReservationItem, form=ReservationItemForm, extra=1, can_delete=True
    )
    # Récupérer le customer_id depuis les paramètres GET
    customer_id = request.GET.get("customer_id")
    initial_data = {}

    if customer_id:
        try:
            from ui.customer.models import Customer

            customer = Customer.objects.get(pk=customer_id)
            initial_data["customer"] = customer
        except Customer.DoesNotExist:
            pass

    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.created_by = request.user
            formset = ReservationItemFormSet(request.POST, instance=reservation)
            if formset.is_valid():
                if formset.total_form_count() == 0:
                    messages.error(
                        request,
                        _("Veuillez ajouter au moins un article à la réservation."),
                    )
                    return redirect("ui:reservation_create")
                with transaction.atomic():
                    reservation = form.save()
                    reservation.created_by = request.user
                    reservation.save()
                    for form in formset:
                        if form.is_valid() and not form.cleaned_data.get("DELETE"):
                            # Ne pas enregistrer les articles avec quantité 0
                            if form.cleaned_data.get("quantity_reserved", 0) > 0:
                                form.save()
                    if formset.is_valid():
                        formset.save()
                        messages.success(request, _("Réservation créée avec succès"))
                        return redirect("ui:reservation_detail", pk=reservation.pk)
        else:
            formset = ReservationItemFormSet(request.POST)
    else:
        form = ReservationForm(initial=initial_data)
        formset = ReservationItemFormSet()

    context = {
        "form": form,
        "formset": formset,
        "categories": Category.objects.all(),
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_form.html", context)


@login_required
@user_type_required("manager")
def reservation_validate(request, pk):
    """
    Validate a reservation, changing its status to 'validated'.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to validate
    :return: Rendered confirmation page or redirect on success
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.status != "created":
        messages.error(request, _("Cette réservation ne peut pas être validée"))
        return redirect("ui:reservation_detail", pk=reservation.pk)

    if request.method == "POST":
        reservation.status = "validated"
        reservation.validated_at = timezone.now()
        reservation.validated_by = request.user
        reservation.save()
        messages.success(request, _("Réservation validée avec succès"))
        return redirect("ui:reservation_detail", pk=reservation.pk)

    context = {
        "reservation": reservation,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_confirm_validate.html", context)


@login_required
@user_type_required("manager")
def reservation_update(request, pk):
    """
    Update an existing reservation.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to update
    :return: Rendered reservation update form or redirect on success
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.status in ["checked_out", "returned"]:
        messages.error(
            request, _("Impossible de modifier une réservation sortie ou rendue")
        )
        return redirect("ui:reservation_detail", pk=reservation.pk)

    ReservationItemFormSet = inlineformset_factory(
        Reservation, ReservationItem, form=ReservationItemForm, extra=1, can_delete=True
    )

    if request.method == "POST":
        form = ReservationForm(request.POST, instance=reservation)
        formset = ReservationItemFormSet(request.POST, instance=reservation)
        if form.is_valid() and formset.is_valid():

            if formset.total_form_count() == 0:
                messages.error(
                    request, _("Veuillez ajouter au moins un article à la réservation.")
                )
                return redirect("ui:reservation_update", pk=reservation.pk)
            with transaction.atomic():
                reservation = form.save()
                submitted_ids = [
                    form.cleaned_data.get("id").pk
                    for form in formset.forms
                    if form.cleaned_data.get("id")
                ]

                ReservationItem.objects.filter(reservation=reservation).exclude(
                    pk__in=submitted_ids
                ).delete()

                for form in formset:
                    if form.is_valid() and not form.cleaned_data.get("DELETE"):
                        if form.cleaned_data.get("quantity_reserved", 0) > 0:
                            form.save()
                if formset.is_valid():
                    formset.save()
                    messages.success(request, _("Réservation modifiée avec succès"))
                    return redirect("ui:reservation_detail", pk=reservation.pk)
    else:
        form = ReservationForm(instance=reservation)
        formset = ReservationItemFormSet(instance=reservation)

    context = {
        "form": form,
        "formset": formset,
        "reservation": reservation,
        "categories": Category.objects.all(),
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_form.html", context)


@login_required
@user_type_required("manager")
def reservation_cancel(request, pk):
    """
    Cancel a reservation, changing its status to 'cancelled'.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to cancel
    :return: Rendered confirmation page or redirect on success
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.status not in ["created", "validated"]:
        messages.error(
            request,
            _(
                "Seules les réservations à l'état 'créée' ou 'validée' peuvent être annulées"
            ),
        )
        return redirect("ui:reservation_detail", pk=reservation.pk)

    if request.method == "POST":
        reservation.status = "cancelled"
        reservation.cancelled_by = request.user
        reservation.cancelled_at = timezone.now()
        reservation.save()
        messages.success(request, _("Réservation annulée avec succès"))
        return redirect("ui:reservations")

    context = {
        "reservation": reservation,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_confirm_cancel.html", context)


@login_required
@user_type_required("manager")
def reservation_checkout(request, pk):
    """
    Check out items for a reservation, updating stock and reservation status.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to check out
    :return: Rendered checkout form or redirect on success
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.status not in ["created", "validated"]:
        messages.error(request, _("Cette réservation ne peut pas être sortie"))
        return redirect("ui:reservation_detail", pk=reservation.pk)

    items = reservation.items.all().order_by("asset__category__name", "asset__name")

    # Verify membership status
    customer_membership = reservation.customer.get_has_paid_membership_fee(
        reservation.checkout_date.year
    )
    customer_membership_fee = reservation.customer.get_membership_fee(
        reservation.checkout_date.year
    )

    if request.method == "POST":
        with transaction.atomic():
            errors = False
            for item in items:
                quantity_key = f"checkout_{item.id}"
                if quantity_key in request.POST:
                    quantity = int(request.POST.get(quantity_key, 0))
                    if quantity > item.asset.stock_quantity:
                        messages.error(
                            request,
                            _(
                                f"Quantité insuffisante pour {item.asset.name} (disponible: {item.asset.stock_quantity})"
                            ),
                        )
                        errors = True
                    else:
                        item.quantity_checked_out = quantity
                        item.save()

                        asset = item.asset
                        asset.stock_quantity -= quantity
                        asset.save()

            if not errors:
                reservation.status = "checked_out"
                reservation.checkout_by = request.user
                actual_date = request.POST.get("actual_checkout_date")
                if actual_date:
                    reservation.actual_checkout_date = actual_date
                else:
                    reservation.actual_checkout_date = timezone.now()
                reservation.notes = request.POST.get("notes", reservation.notes)
                reservation.save()

                messages.success(request, _("Sortie de matériel effectuée avec succès"))
                return redirect("ui:reservation_detail", pk=reservation.pk)

    context = {
        "reservation": reservation,
        "items": items,
        "total_expected": reservation.total_expected_donation,
        "customer_membership": customer_membership,
        "customer_membership_fee": customer_membership_fee,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_checkout.html", context)


@login_required
@user_type_required("manager")
def reservation_return(request, pk):
    """
    Process the return of items for a reservation, updating stock and reservation status.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to return
    :return: Rendered return form or redirect on success
    """
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.status != "checked_out":
        messages.error(request, _("Cette réservation ne peut pas être retournée"))
        return redirect("ui:reservation_detail", pk=reservation.pk)

    items = reservation.items.filter(quantity_checked_out__gt=0).order_by(
        "asset__category__name", "asset__name"
    )

    if request.method == "POST":
        with transaction.atomic():
            for item in items:
                return_key = f"return_{item.id}"
                damaged_key = f"damaged_{item.id}"
                destroyed_key = f"destroyed_{item.id}"

                if (
                    return_key in request.POST
                    and damaged_key in request.POST
                    and destroyed_key in request.POST
                ):
                    returned_qty = int(request.POST.get(return_key, 0))
                    damaged_qty = int(request.POST.get(damaged_key, 0))
                    destroyed_qty = int(request.POST.get(destroyed_key, 0))

                    total_returned = returned_qty + damaged_qty + destroyed_qty
                    if total_returned > item.quantity_checked_out:
                        messages.error(
                            request, _(f"Quantités invalides pour {item.asset.name}")
                        )
                        break

                    item.quantity_returned = returned_qty
                    item.quantity_damaged = damaged_qty
                    item.notes = (
                        f"Détruits: {destroyed_qty}" if destroyed_qty > 0 else ""
                    )
                    item.save()

                    asset = item.asset
                    asset.stock_quantity += returned_qty
                    asset.save()
            else:
                total_donations = float(request.POST.get("total_donations", 0))
                customer_membership = reservation.customer.get_has_paid_membership_fee(
                    reservation.true_return_date.year
                )

                if total_donations > 0:
                    includes_membership = not customer_membership
                    Donation.objects.create(
                        customer=reservation.customer,
                        amount=total_donations,
                        includes_membership=includes_membership,
                        reservation=reservation,
                    )
                reservation.status = "returned"
                reservation.returned_by = request.user

                actual_date = request.POST.get("actual_return_date")
                if actual_date:
                    reservation.actual_return_date = actual_date
                else:
                    reservation.actual_return_date = timezone.now()

                reservation.save()

                messages.success(
                    request, _("Retour de matériel enregistré avec succès")
                )
                return redirect("ui:reservation_detail", pk=reservation.pk)
    customer_membership = reservation.customer.get_has_paid_membership_fee(
        reservation.checkout_date.year
    )
    customer_membership_fee = reservation.customer.get_membership_fee(
        reservation.checkout_date.year
    )
    context = {
        "reservation": reservation,
        "items": items,
        "total_expected": reservation.total_expected_donation,
        "customer_membership": customer_membership,
        "customer_membership_fee": customer_membership_fee,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_return.html", context)


@login_required
@user_type_required("manager")
def reservation_pdf(request, pk):
    """
    Generate a PDF summary of the reservation, including a QR code linking to its detail page.
    :param request: HTTP request object
    :param pk: Primary key of the reservation to generate PDF for
    :return: PDF file as HTTP response
    """
    reservation = get_object_or_404(Reservation, pk=pk)
    items = reservation.items.all().order_by("asset__category__name", "asset__name")
    detail_url = request.build_absolute_uri(
        reverse("ui:reservation_detail", args=[reservation.pk])
    )
    qr = qrcode.make(detail_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    logo_path = Path(settings.BASE_DIR) / "static" / "images" / "cdf_black.png"
    context = {
        "reservation": reservation,
        "items": items,
        "qr_base64": qr_base64,
        "logo_path": f"file:{logo_path}",
        "capability": get_capability(request.user),
    }
    html_string = render_to_string("ui/reservations/pdf_summary.html", context)
    pdf_file = HTML(
        string=html_string, base_url=request.build_absolute_uri()
    ).write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="reservation_{reservation.pk}.pdf"'
    )
    return response


def search_assets(request):
    """
    Search for assets based on query parameters, returning JSON results.
    :param request: HTTP request object
    :return: JSON response with search results
    """
    query = request.GET.get("q", "")
    category_id = request.GET.get("category", None)
    excluded_ids = request.GET.getlist("exclude[]", [])
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", None)

    assets = Asset.objects.filter(stock_quantity__gt=0)

    if start_date == "":
        start_date = timezone.now()
    else:
        start_date = datetime.datetime.fromisoformat(start_date)
    if end_date is not None:
        end_date = datetime.datetime.fromisoformat(end_date)

    if category_id:
        assets = assets.filter(category_id=category_id)

    if query:
        assets = assets.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if excluded_ids:
        assets = assets.exclude(id__in=excluded_ids)

    assets = assets.order_by("category__name", "name")
    results = []
    for asset in assets:
        r_asset = {
            "id": asset.id,
            "text": asset.name,
            "category": asset.category.name,
            "rental_value": float(asset.rental_value),
        }
        if end_date:
            quantities = analyze_asset_availability(asset, Period(start_date, end_date))
        else:
            quantities = get_asset_status_at_date(asset, start_date)
        r_asset["stock"] = quantities["available"]
        r_asset["stock_total"] = quantities["total"]
        r_asset["stock_damaged"] = quantities["damaged"]
        r_asset["stock_checked_out"] = quantities["checked_out"]
        r_asset["stock_reserved"] = quantities["reserved"]
        results.append(r_asset)

    return JsonResponse({"results": results})


def check_reservation(request):
    """
    Check the availability of items in a reservation.
    :param request: HTTP request object
    :return: JSON response with availability status
    """
    res_pk = request.GET.get("res_pk", "")
    response = {"is_ok": False, "problematic_items": []}
    if not res_pk:
        return JsonResponse(response, status=200)
    reservation = get_object_or_404(Reservation, pk=res_pk)
    response = check_reservation_availability(reservation)
    return JsonResponse(response, status=200)


@login_required
@user_type_required("manager")
def reservation_calendar_data(request):
    """
    Provide reservation data in JSON format for calendar display.
    :param request: HTTP request object
    :return: JSON response with reservation events
    """

    active_only = request.GET.get("active_only", "false")
    reservations_query = Reservation.objects.all()
    filters = {}

    if active_only == "true":
        filters["status__in"] = ["created", "validated", "checked_out"]
    else:
        filters["status__in"] = ["created", "validated", "checked_out", "returned"]

    reservations = reservations_query.filter(**filters)

    events = []

    for reservation in reservations:
        items_text = ", ".join(
            [
                f"{item.asset.name} ({item.quantity_reserved})"
                for item in reservation.items.all()[:3]
            ]
        )

        if reservation.items.count() > 3:
            items_text += "..."

        description = f"""
                <strong>Client:</strong> {reservation.customer}<br>
                <strong>Statut:</strong> {reservation.get_status_display()}<br>
                <strong>Articles:</strong> {items_text}<br>
                <strong>Don:</strong> {reservation.total_donations} €
            """

        resource_id = f"customer-{reservation.customer}"
        check_result = check_reservation_availability(reservation)
        events.append(
            {
                "id": reservation.id,
                "resourceId": resource_id,
                "title": f"{reservation.customer}",
                "start": reservation.true_start_date.isoformat(),
                "end": reservation.true_return_date.isoformat(),
                "url": reverse("ui:reservation_detail", args=[reservation.id]),
                "extendedProps": {
                    "customer": str(reservation.customer),
                    "status": str(reservation.get_status_display()),
                    "status_raw": reservation.status,
                    "items": items_text,
                    "description": description,
                    "is_problematic": not check_result["is_ok"],
                },
            }
        )

    return JsonResponse(events, safe=False)
