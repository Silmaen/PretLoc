"""
Views for managing stock items, categories, and stock events.
"""

import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import user_type_required, get_capability
from ui.reservation.models import Reservation
from utils.computations import get_asset_status_at_date
from .forms import (
    CategoryForm,
    AssetForm,
    StockEventForm,
)
from .models import (
    Category,
    Asset,
)


@login_required
@user_type_required("member")
def stock_view(request):
    """
    Main view for displaying and managing stock items.
    :param request: HTTP request object
    :return: Rendered stock list page
    """
    categories = Category.objects.all().order_by("name")
    category_id = request.GET.get("category")
    sort = request.GET.get("sort", "name")
    direction = request.GET.get("direction", "asc")
    search_query = request.GET.get("search", "")

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

    if sort == "category":
        order_by = "category__name"
    else:
        order_by = "name"

    if direction == "desc":
        order_by = f"-{order_by}"

    filters = {}

    if category_id not in [None, "", "None"]:
        filters["category_id"] = category_id
        current_category = get_object_or_404(Category, id=category_id)
    else:
        category_id = None
        current_category = None

    if search_query:
        items = Asset.objects.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query),
            **filters,
        ).order_by(order_by)
    else:
        items = Asset.objects.filter(**filters).order_by(order_by)

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


@login_required
@user_type_required("member")
def category_list(request):
    """
    View to list all categories.
    :param request: HTTP request object
    :return: Rendered category list page
    """
    categories = Category.objects.all().order_by("name")
    context = {
        "categories": categories,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/stock/category_list.html", context)


@login_required
@user_type_required("admin")
def category_create(request):
    """
    Create a new category.
    :param request: HTTP request object
    :return: Rendered category creation form or redirect on success
    """
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
    """
    Update an existing category.
    :param request: HTTP request object
    :param pk: Primary key of the category to update
    :return: Rendered category update form or redirect on success
    """
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
    """
    Delete an existing category.
    :param request: HTTP request object
    :param pk: Primary key of the category to delete
    :return: Rendered category deletion confirmation or redirect on success
    """
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
    """
    View to create a new stock item.
    :param request: HTTP request object
    :return: Rendered item creation form or redirect on success
    """
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
    """
    View to update an existing stock item.
    :param request: HTTP request object
    :param pk: Primary key of the item to update
    :return: Rendered item update form or redirect on success
    """
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
    """
    View to delete an existing stock item.
    :param request: HTTP request object
    :param pk: Primary key of the item to delete
    :return: Rendered item deletion confirmation or redirect on success
    """
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
    """
    View to display details of a stock item, including stock events and reservations.
    :param request: HTTP request object
    :param pk: Primary key of the item to display
    :return: Rendered item detail page
    """
    item = get_object_or_404(Asset, pk=pk)

    end_date = request.GET.get("end_date", timezone.now().strftime("%Y-%m-%dT%H:%M"))
    start_date = request.GET.get(
        "start_date",
        (timezone.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M"),
    )

    quantities = get_asset_status_at_date(item)

    try:
        start_date_obj = timezone.make_aware(
            datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M")
        )
        end_date_obj = timezone.make_aware(
            datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M")
        )
        end_date_obj = timezone.make_aware(
            end_date_obj.replace(hour=23, minute=59, second=59)
        )
    except ValueError:
        start_date_obj = timezone.now() - datetime.timedelta(days=365)
        end_date_obj = timezone.now()
        start_date = start_date_obj.strftime("%Y-%m-%dT%H:%M")
        end_date = end_date_obj.strftime("%Y-%m-%dT%H:%M")

    stock_events = item.stockevent_set.filter(
        date__gte=start_date_obj, date__lte=end_date_obj
    ).order_by("-date")

    reservations = (
        Reservation.objects.filter(
            items__asset=item,
            status__in=["checked_out", "returned"],
            actual_checkout_date__isnull=False,
        )
        .filter(
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
@user_type_required("manager")
def stock_event_create(request, asset_id=None):
    """
    Create a new stock event, optionally linked to a specific asset.
    :param request: HTTP request object
    :param asset_id: Optional primary key of the asset to link the event to
    :return: Rendered stock event creation form or redirect on success
    """
    initial = {}
    if asset_id:
        asset = get_object_or_404(Asset, pk=asset_id)
        initial["asset"] = asset

    if request.method == "POST":
        form = StockEventForm(request.POST, initial=initial)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user

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
