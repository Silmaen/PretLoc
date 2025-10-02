"""
views.py

defines the views for the UI application, including a health check endpoint.
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
from django.db.models.deletion import ProtectedError
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
from .computations import (
    get_asset_status_at_date,
    analyze_asset_availability,
    check_reservation_availability,
)
from .forms import (
    CategoryForm,
    AssetForm,
    CustomerForm,
    CustomerTypeForm,
    ReservationForm,
    ReservationItemForm,
    StockEventForm,
)
from .models import (
    Category,
    Asset,
    Customer,
    Reservation,
    ReservationItem,
    CustomerType,
)


def health_check(request):
    return HttpResponse("OK", status=200)


def home(request):
    return redirect("ui:reservations")
    # return render(request, "ui/home.html", {"capability": get_capability(request.user)})


@login_required
@user_type_required("member")
def stock_view(request):
    """Vue principale pour la page de gestion du stock"""
    categories = Category.objects.all().order_by("name")
    category_id = request.GET.get("category")
    sort = request.GET.get("sort", "name")  # Par défaut, tri par nom
    direction = request.GET.get("direction", "asc")  # Par défaut, ordre ascendant
    search_query = request.GET.get("search", "")  # Récupération de la recherche

    # Récupérer la date sélectionnée ou utiliser la date actuelle par défaut
    stock_date = request.GET.get("stock_date")
    if stock_date:
        try:
            stock_date = timezone.make_aware(
                datetime.datetime.strptime(stock_date, "%Y-%m-%dT%H:%M")
            )
        except ValueError:
            stock_date = timezone.now()
    else:
        stock_date = timezone.now()

    # Déterminer le champ de tri
    if sort == "category":
        order_by = "category__name"  # Pour trier par nom de catégorie
    else:
        order_by = "name"  # Par défaut, tri par nom d'article

    # Appliquer la direction du tri
    if direction == "desc":
        order_by = f"-{order_by}"

    # Initialiser les filtres de base
    filters = {}

    # Filtrer par catégorie si spécifiée
    if category_id not in [None, "", "None"]:
        filters["category_id"] = category_id
        current_category = get_object_or_404(Category, id=category_id)
    else:
        category_id = None
        current_category = None

    # Filtrer par recherche si spécifiée
    if search_query:
        items = Asset.objects.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query),
            **filters,
        ).order_by(order_by)
    else:
        items = Asset.objects.filter(**filters).order_by(order_by)

    # Calculer l'état du stock pour chaque article à la date spécifiée
    for item in items:
        item.stock_status = get_asset_status_at_date(item, stock_date)

    context = {
        "items": items,
        "categories": categories,
        "current_category": current_category,
        "category_id": category_id,
        "sort": sort,
        "direction": direction,
        "search_query": search_query,  # Ajouter la recherche au contexte
        "stock_date": stock_date,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/stock/list.html", context)


# Vues pour la gestion des catégories (admin uniquement)
@login_required
@user_type_required("member")
def category_list(request):
    categories = Category.objects.all().order_by("name")
    context = {
        "categories": categories,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/stock/category_list.html", context)


@login_required
@user_type_required("admin")
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie créée avec succès"))
            return redirect("ui:category_list")
    else:
        form = CategoryForm()
    return render(
        request,
        "ui/stock/category_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie modifiée avec succès"))
            return redirect("ui:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(
        request,
        "ui/stock/category_form.html",
        {
            "form": form,
            "category": category,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, _("Catégorie supprimée avec succès"))
        return redirect("ui:category_list")
    return render(
        request,
        "ui/stock/category_confirm_delete.html",
        {
            "category": category,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def item_create(request):
    if request.method == "POST":
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Article créé avec succès"))
            return redirect("ui:stock")
    else:
        form = AssetForm()
    return render(
        request,
        "ui/stock/item_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
def item_update(request, pk):
    item = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        form = AssetForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, _("Article modifié avec succès"))
            return redirect("ui:stock")
    else:
        form = AssetForm(instance=item)
    return render(
        request,
        "ui/stock/item_form.html",
        {
            "form": form,
            "item": item,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def item_delete(request, pk):
    item = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, _("Article supprimé avec succès"))
        return redirect("ui:stock")
    return render(
        request,
        "ui/stock/item_confirm_delete.html",
        {
            "item": item,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("member")
def item_detail(request, pk):
    """Vue pour afficher les détails d'un article"""

    item = get_object_or_404(Asset, pk=pk)

    # Dates par défaut : maintenant et un an en arrière
    end_date = request.GET.get("end_date", timezone.now().strftime("%Y-%m-%dT%H:%M"))
    start_date = request.GET.get(
        "start_date",
        (timezone.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M"),
    )

    quantities = get_asset_status_at_date(item)

    # Conversion des dates en objets datetime{% endif %}
    # {% endfor %}
    try:
        start_date_obj = timezone.make_aware(
            datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
        )
        end_date_obj = timezone.make_aware(
            datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        )
        # Inclure toute la journée de fin
        end_date_obj = timezone.make_aware(
            end_date_obj.replace(hour=23, minute=59, second=59)
        )
    except ValueError:
        start_date_obj = timezone.now() - datetime.timedelta(days=365)
        end_date_obj = timezone.now()
        start_date = start_date_obj.strftime("%Y-%m-%dT%H:%M")
        end_date = end_date_obj.strftime("%Y-%m-%dT%H:%M")

    # Filtrer les événements de stock par date
    stock_events = item.stockevent_set.filter(
        date__gte=start_date_obj, date__lte=end_date_obj
    ).order_by("-date")

    # Récupérer les réservations terminées ou sorties
    reservations = (
        Reservation.objects.filter(
            items__asset=item,
            status__in=["checked_out", "returned"],
            actual_checkout_date__isnull=False,
        )
        .filter(
            # Date de sortie ou de retour dans l'intervalle
            Q(
                actual_checkout_date__gte=start_date_obj,
                actual_checkout_date__lte=end_date_obj,
            )
            | Q(
                actual_return_date__gte=start_date_obj,
                actual_return_date__lte=end_date_obj,
            )
        )
        .distinct()
        .order_by("-actual_checkout_date")
    )

    context = {
        "item": item,
        "quantities": quantities,
        "stock_events": stock_events,
        "reservations": reservations,
        "start_date": start_date,
        "end_date": end_date,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/stock/item_detail.html", context)


@login_required
@user_type_required("admin")
def customer_type_list(request):
    customer_types = CustomerType.objects.all().order_by("name")
    context = {
        "customer_types": customer_types,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/customers/customer_type_list.html", context)


@login_required
@user_type_required("admin")
def customer_type_create(request):
    if request.method == "POST":
        form = CustomerTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Type de client créé avec succès"))
            return redirect("ui:customer_type_list")
    else:
        form = CustomerTypeForm()
    return render(
        request,
        "ui/customers/customer_type_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def customer_type_update(request, pk):
    customer_type = get_object_or_404(CustomerType, pk=pk)
    if request.method == "POST":
        form = CustomerTypeForm(request.POST, instance=customer_type)
        if form.is_valid():
            form.save()
            messages.success(request, _("Type de client modifié avec succès"))
            return redirect("ui:customer_type_list")
    else:
        form = CustomerTypeForm(instance=customer_type)
    return render(
        request,
        "ui/customers/customer_type_form.html",
        {
            "form": form,
            "customer_type": customer_type,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def customer_type_delete(request, pk):
    customer_type = get_object_or_404(CustomerType, pk=pk)
    if request.method == "POST":
        try:
            customer_type.delete()
            messages.success(request, _("Type de client supprimé avec succès"))
        except ProtectedError:
            messages.error(
                request, _("Ce type de client est utilisé par des clients existants")
            )
        return redirect("ui:customer_type_list")
    return render(
        request,
        "ui/customers/customer_type_confirm_delete.html",
        {
            "customer_type": customer_type,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
def customers_view(request):
    """Vue principale pour la page de gestion des clients"""
    search_query = request.GET.get("search", "")
    customer_type_id = request.GET.get("customer_type", "")
    entity_type = request.GET.get("entity_type", "")
    donation_exemption = request.GET.get("donation_exemption", "")
    sort = request.GET.get("sort", "last_name")  # Par défaut, tri par nom
    direction = request.GET.get("direction", "asc")  # Par défaut, ordre ascendant

    # Déterminer le champ de tri
    order_by = sort

    # Appliquer la direction du tri
    if direction == "desc":
        order_by = f"-{order_by}"

    # Initialiser les filtres de base
    filters = {}

    # Ajouter le filtre par type si spécifié
    if customer_type_id not in ["", None]:
        filters["customer_type_id"] = customer_type_id
    if entity_type in ["physical", "legal"]:
        filters["customer_type__entity_type"] = entity_type
    # Filtrage par exonération de don
    if donation_exemption == "true":
        filters["donation_exemption"] = True
    elif donation_exemption == "false":
        filters["donation_exemption"] = False
    # Filtrer par recherche si spécifiée
    if search_query:
        customers = Customer.objects.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(company_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query),
            **filters,
        ).order_by(order_by)
    else:
        customers = Customer.objects.filter(**filters).order_by(order_by)

    customer_types = CustomerType.objects.all().order_by("name")

    context = {
        "customers": customers,
        "customer_types": customer_types,
        "search_query": search_query,
        "customer_type_id": customer_type_id,
        "entity_type": entity_type,
        "donation_exemption": donation_exemption,
        "sort": sort,
        "direction": direction,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/customers/list.html", context)


@login_required
@user_type_required("manager")
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Client créé avec succès"))
            return redirect("ui:customers")
    else:
        form = CustomerForm()
    return render(
        request,
        "ui/customers/customer_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, _("Client modifié avec succès"))
            return redirect("ui:customers")
    else:
        form = CustomerForm(instance=customer)
    return render(
        request,
        "ui/customers/customer_form.html",
        {
            "form": form,
            "customer": customer,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, _("Client supprimé avec succès"))
        return redirect("ui:customers")
    return render(
        request,
        "ui/customers/customer_confirm_delete.html",
        {
            "customer": customer,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
def reservation_list(request):
    """Vue pour afficher la liste des réservations"""
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    sort = request.GET.get("sort", "checkout_date")
    direction = request.GET.get("direction", "desc")
    active_only = request.GET.get("active_only", "false")

    # Déterminer le champ de tri
    order_by = sort

    # Cas spécial pour le tri par statut (ordre personnalisé)
    if sort == "status":

        # Définir l'ordre personnalisé: created, validated, checked_out, returned, cancelled
        status_order = {
            "created": 1,
            "validated": 2,
            "checked_out": 3,
            "returned": 4,
            "cancelled": 5,
        }

        # Utiliser Case/When pour trier avec un ordre personnalisé
        status_ordering = Case(
            *[When(status=k, then=Value(v)) for k, v in status_order.items()],
            output_field=IntegerField(),
        )

        # Appliquer la direction du tri
        if direction == "desc":
            status_ordering = status_ordering.desc()

        # Utiliser annotate pour créer un champ temporaire pour le tri
        reservations_query = Reservation.objects.annotate(status_order=status_ordering)
        order_by = "status_order"
    else:
        reservations_query = Reservation.objects.all()
        # Appliquer la direction du tri
        if direction == "desc" and sort != "status":
            order_by = f"-{order_by}"

    # Initialiser les filtres de base
    filters = {}

    # Filtrer par statut si spécifié
    if status_filter:
        filters["status"] = status_filter

    # Filtrer pour n'afficher que les réservations actives si demandé
    if active_only == "true":
        if "status" in filters:
            # Si un filtre de statut est déjà appliqué, vérifier qu'il est compatible
            if filters["status"] not in ["returned", "cancelled"]:
                # Le filtre de statut est compatible, pas besoin d'autres filtres
                pass
            else:
                # Le filtre de statut est incompatible avec active_only, ignorer active_only
                active_only = "false"
        else:
            # Pas de filtre de statut spécifique, exclure les statuts "returned" et "cancelled"
            filters["status__in"] = ["created", "validated", "checked_out"]

    # Filtrer par recherche si spécifiée
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
    """Vue pour afficher les détails d'une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)
    items = reservation.items.all().order_by("asset__category__name", "asset__name")

    if reservation.status in ["created", "validated"]:
        # Calculer la disponibilité des articles pour les réservations en cours
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

    context = {
        "reservation": reservation,
        "items": items,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/detail.html", context)


@login_required
@user_type_required("manager")
def reservation_create(request):
    """Vue pour créer une nouvelle réservation"""
    ReservationItemFormSet = inlineformset_factory(
        Reservation, ReservationItem, form=ReservationItemForm, extra=1, can_delete=True
    )

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
        form = ReservationForm()
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
    """Vue pour valider une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)

    # Vérifier si la réservation peut être validée
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
    """Vue pour modifier une réservation existante"""
    reservation = get_object_or_404(Reservation, pk=pk)

    # Ne pas autoriser les modifications pour les réservations déjà sorties ou rendues
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
                # Récupérer les IDs des éléments soumis
                submitted_ids = [
                    form.cleaned_data.get("id").pk
                    for form in formset.forms
                    if form.cleaned_data.get("id")
                ]

                # Supprimer les éléments manquants
                ReservationItem.objects.filter(reservation=reservation).exclude(
                    pk__in=submitted_ids
                ).delete()

                for form in formset:
                    if form.is_valid() and not form.cleaned_data.get("DELETE"):
                        # Ne pas enregistrer les articles avec quantité 0
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
    """Vue pour annuler une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)

    # Ne permettre l'annulation que pour les réservations en état "created" ou "validated"
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
    """Vue pour effectuer une sortie de matériel"""
    reservation = get_object_or_404(Reservation, pk=pk)

    # Vérifier si la réservation peut être passée en statut "sortie"
    if reservation.status not in ["created", "validated"]:
        messages.error(request, _("Cette réservation ne peut pas être sortie"))
        return redirect("ui:reservation_detail", pk=reservation.pk)

    items = reservation.items.all().order_by("asset__category__name", "asset__name")

    if request.method == "POST":
        with transaction.atomic():
            # Mettre à jour les quantités sorties pour chaque article
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

                        # Mettre à jour le stock
                        asset = item.asset
                        asset.stock_quantity -= quantity
                        asset.save()

            if not errors:
                # Mettre à jour le statut de la réservation
                reservation.status = "checked_out"
                reservation.checkout_by = request.user
                # Enregistrer la date réelle de sortie
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
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_checkout.html", context)


@login_required
@user_type_required("manager")
def reservation_return(request, pk):
    """Vue pour enregistrer un retour de matériel"""
    reservation = get_object_or_404(Reservation, pk=pk)

    # Vérifier si la réservation peut être retournée
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

                    # Vérifier que les quantités sont valides
                    total_returned = returned_qty + damaged_qty + destroyed_qty
                    if total_returned > item.quantity_checked_out:
                        messages.error(
                            request, _(f"Quantités invalides pour {item.asset.name}")
                        )
                        break

                    # Mettre à jour les quantités
                    item.quantity_returned = returned_qty
                    item.quantity_damaged = damaged_qty
                    # Ajouter un champ pour les articles détruits ou créer une note
                    item.notes = (
                        f"Détruits: {destroyed_qty}" if destroyed_qty > 0 else ""
                    )
                    item.save()

                    # Remettre en stock uniquement les articles en bon état
                    asset = item.asset
                    asset.stock_quantity += returned_qty
                    asset.save()
            else:  # Ce bloc s'exécute si la boucle se termine normalement (sans break)
                # Mettre à jour le statut de la réservation
                donation = float(request.POST.get("donation_amount", 0))
                reservation.donation_amount = donation
                reservation.status = "returned"
                reservation.returned_by = request.user

                # Enregistrer la date réelle de retour
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

    context = {
        "reservation": reservation,
        "items": items,
        "total_expected": reservation.total_expected_donation,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/reservations/reservation_return.html", context)


@login_required
@user_type_required("manager")
def reservation_pdf(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    items = reservation.items.all().order_by("asset__category__name", "asset__name")
    # Générer l'URL de détail
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


@login_required
@user_type_required("manager")
def stock_event_create(request, asset_id=None):
    """Vue pour créer un nouvel événement de stock"""
    initial = {}
    if asset_id:
        asset = get_object_or_404(Asset, pk=asset_id)
        initial["asset"] = asset

    if request.method == "POST":
        form = StockEventForm(request.POST, initial=initial)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user

            # Sauvegarder les changements
            with transaction.atomic():
                event.save()

            messages.success(request, _("Événement de stock enregistré avec succès"))
            return redirect("ui:stock")
    else:
        form = StockEventForm(initial=initial)

    return render(
        request,
        "ui/stock/stock_event_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
def search_customers(request):
    search_query = request.GET.get("q", "")
    page = int(request.GET.get("page", 1))
    page_size = 10

    offset = (page - 1) * page_size

    customers = Customer.objects.filter(
        Q(last_name__icontains=search_query)
        | Q(first_name__icontains=search_query)
        | Q(company_name__icontains=search_query)
        | Q(email__icontains=search_query)
    ).order_by("last_name", "company_name")[offset : offset + page_size + 1]

    has_more = len(customers) > page_size
    if has_more:
        customers = customers[:page_size]

    results = [
        {
            "id": c.id,
            "text": str(c),
            "email": c.email,  # Ajoutez d'autres champs si nécessaire
        }
        for c in customers
    ]

    return JsonResponse({"results": results, "has_more": has_more})


def search_assets(request):
    query = request.GET.get("q", "")
    category_id = request.GET.get("category", None)
    # Récupérer les IDs d'articles déjà dans la réservation
    excluded_ids = request.GET.getlist("exclude[]", [])
    start_date = request.GET.get("start_date", timezone.now())
    end_date = request.GET.get("end_date", None)

    assets = Asset.objects.filter(stock_quantity__gt=0)

    # Filtrage par catégorie
    if category_id and category_id.isdigit():
        assets = assets.filter(category_id=int(category_id))

    # Recherche par nom ou description
    if query:
        assets = assets.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Exclure les articles déjà sélectionnés
    if excluded_ids:
        assets = assets.exclude(id__in=excluded_ids)

    # Trier par catégorie puis par nom
    assets = assets.order_by("category__name", "name")
    # Limiter les résultats et formater la réponse
    results = []
    for asset in assets:
        r_asset = {
            "id": asset.id,
            "text": asset.name,
            "category": asset.category.name,
            "rental_value": float(asset.rental_value),
        }
        if end_date:
            # Calculer les quantités disponibles à la date de fin
            quantities = analyze_asset_availability(asset, start_date, end_date)
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
    res_pk = request.GET.get("res_pk", "")
    response = {"is_ok": False, "problematic_items": []}
    if not res_pk:
        # plus tard, on pourra tester toutes les réservations, ou les filtrer par date...
        return JsonResponse(response, status=200)
    reservation = get_object_or_404(Reservation, pk=res_pk)
    response = check_reservation_availability(reservation)
    return JsonResponse(response, status=200)


@login_required
@user_type_required("manager")
def reservation_calendar_data(request):
    """Retourne les données des réservations pour le calendrier."""

    active_only = request.GET.get("active_only", "false")
    reservations_query = Reservation.objects.all()
    # Initialiser les filtres de base
    filters = {}

    if active_only == "true":
        # Pas de filtre de statut spécifique, exclure les statuts "returned" et "cancelled"
        filters["status__in"] = ["created", "validated", "checked_out"]
    else:
        filters["status__in"] = ["created", "validated", "checked_out", "returned"]

    reservations = reservations_query.filter(**filters)

    events = []

    for reservation in reservations:
        # Récupérer les items pour affichage dans le tooltip
        items_text = ", ".join(
            [
                f"{item.asset.name} ({item.quantity_reserved})"
                for item in reservation.items.all()[:3]
            ]
        )

        if reservation.items.count() > 3:
            items_text += "..."

        # Formatage de la description complète pour le tooltip
        description = f"""
                <strong>Client:</strong> {reservation.customer}<br>
                <strong>Statut:</strong> {reservation.get_status_display()}<br>
                <strong>Articles:</strong> {items_text}<br>
                <strong>Don:</strong> {reservation.donation_amount} €
            """

        # Formatage du titre plus simple pour l'affichage
        # title = f"{reservation.get_status_display()}"

        # ID ressource pour grouper par client
        resource_id = f"customer-{reservation.customer}"
        check_result = check_reservation_availability(reservation)
        events.append(
            {
                "id": reservation.id,
                "resourceId": resource_id,
                "title": f"{reservation.customer}",
                "start": reservation.get_start_date().isoformat(),
                "end": reservation.get_return_date().isoformat(),
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
