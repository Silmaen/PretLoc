"""
Views for managing donations.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from accounts.decorators import user_type_required, get_capability
from ui.customer.models import Customer
from .forms import DonationForm
from .models import Donation

logger = logging.getLogger(__name__)


@login_required
@user_type_required("manager")
def donation_list(request):
    """
    Display a list of donations with filtering and searching capabilities.
    :param request: HTTP request object
    :return: Rendered donation list page
    """
    search_query = request.GET.get("search", "")
    includes_membership = request.GET.get("includes_membership", "")
    sort = request.GET.get("sort", "-date")

    donations = Donation.objects.select_related("customer", "reservation")

    # Filtres
    if includes_membership:
        donations = donations.filter(
            includes_membership=(includes_membership == "true")
        )

    # Recherche
    if search_query:
        donations = donations.filter(
            Q(customer__last_name__icontains=search_query)
            | Q(customer__first_name__icontains=search_query)
            | Q(customer__company_name__icontains=search_query)
            | Q(customer__email__icontains=search_query)
        )

    # Tri
    donations = donations.order_by(sort)

    # Calcul du total
    total_donations = sum(donation.amount for donation in donations)

    context = {
        "donations": donations,
        "search_query": search_query,
        "includes_membership": includes_membership,
        "sort": sort,
        "total_donations": total_donations,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/donations/list.html", context)


@login_required
@user_type_required("manager")
def donation_create(request):
    """
    Create a new donation.
    :param request: HTTP request object
    :return: Rendered donation creation form or redirect on success
    """

    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save()
            messages.success(request, _("Don créé avec succès"))
            return redirect("ui:donation_list")
    else:
        customer_id = request.GET.get("customer_id")
        initial_data = {}
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                initial_data["customer"] = customer
            except Customer.DoesNotExist:
                logger.warning(f"Customer not found for ID {customer_id}")
                pass
        else:
            logger.debug("No customer_id provided in GET parameters")
        form = DonationForm(initial=initial_data)

    context = {
        "form": form,
        "title": _("Créer un don"),
        "capability": get_capability(request.user),
    }
    return render(request, "ui/donations/form.html", context)


@login_required
@user_type_required("manager")
def donation_update(request, pk):
    """
    Update an existing donation.
    :param request: HTTP request object
    :param pk: Primary key of the donation to update
    :return: Rendered donation update form or redirect on success
    """
    donation = get_object_or_404(Donation, pk=pk)

    if request.method == "POST":
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, _("Don modifié avec succès"))
            return redirect("ui:donation_list")
    else:
        form = DonationForm(instance=donation)

    context = {
        "form": form,
        "donation": donation,
        "title": _("Modifier le don"),
        "capability": get_capability(request.user),
    }
    return render(request, "ui/donations/form.html", context)


@login_required
@user_type_required("manager")
def donation_delete(request, pk):
    """
    Delete a donation.
    :param request: HTTP request object
    :param pk: Primary key of the donation to delete
    :return: Rendered confirmation page or redirect on success
    """
    donation = get_object_or_404(Donation, pk=pk)

    if request.method == "POST":
        donation.delete()
        messages.success(request, _("Don supprimé avec succès"))
        return redirect("ui:donation_list")

    context = {
        "donation": donation,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/donations/confirm_delete.html", context)
