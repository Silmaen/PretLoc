"""
views.py

defines the views for the UI application, including a health check endpoint.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from accounts.decorators import user_type_required, get_capability
from .forms import CategoryForm, AssetForm
from .models import Category, Asset


def health_check(request):
    return HttpResponse("OK", status=200)


def home(request):
    return render(request, "ui/home.html", {"capability": get_capability(request.user)})


@login_required
@user_type_required("member")
def stock_view(request):
    """Vue principale pour la page de gestion du stock"""
    categories = Category.objects.all().order_by("name")
    category_id = request.GET.get("category")
    sort = request.GET.get("sort", "name")  # Par défaut, tri par nom
    direction = request.GET.get("direction", "asc")  # Par défaut, ordre ascendant

    # Déterminer le champ de tri
    if sort == "category":
        order_by = "category__name"  # Pour trier par nom de catégorie
    else:
        order_by = "name"  # Par défaut, tri par nom d'article

    # Appliquer la direction du tri
    if direction == "desc":
        order_by = f"-{order_by}"

    # Filtrer par catégorie si spécifiée
    if category_id:
        items = Asset.objects.filter(category_id=category_id).order_by(order_by)
        current_category = get_object_or_404(Category, id=category_id)
    else:
        items = Asset.objects.all().order_by(order_by)
        current_category = None

    context = {
        "items": items,
        "categories": categories,
        "current_category": current_category,
        "category_id": category_id,
        "sort": sort,
        "direction": direction,
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
