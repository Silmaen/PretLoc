"""
Views for managing customers and customer types.
"""

from datetime import datetime

from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from accounts.decorators import get_capability, user_capability_required
from .forms import (
    CustomerForm,
    CustomerTypeForm,
)
from .models import (
    Customer,
    CustomerType,
)


@user_capability_required("can_view_customer_types")
def customer_type_list(request):
    """
    List all customer types.
    :param request: HTTP request object
    :return: Rendered customer type list page
    """
    customer_types = CustomerType.objects.all().order_by("name")
    context = {
        "customer_types": customer_types,
        "capability": get_capability(request.user),
    }
    return render(request, "ui/customers/type/customer_type_list.html", context)


@user_capability_required("can_add_customer_types")
def customer_type_create(request):
    """
    Create a new customer type.
    :param request: HTTP request object
    :return: Rendered customer type creation form or redirect on success
    """
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
        "ui/customers/type/customer_type_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@user_capability_required("can_edit_customer_types")
def customer_type_update(request, pk):
    """
    Update an existing customer type.
    :param request: HTTP request object
    :param pk: Primary key of the customer type to update
    :return: Rendered customer type update form or redirect on success
    """
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
        "ui/customers/type/customer_type_form.html",
        {
            "form": form,
            "customer_type": customer_type,
            "capability": get_capability(request.user),
        },
    )


@user_capability_required("can_delete_customer_types")
def customer_type_delete(request, pk):
    """
    Delete a customer type after confirming.
    :param request: HTTP request object
    :param pk: Primary key of the customer type to delete
    :return: Rendered confirmation page or redirect on success
    """
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
        "ui/customers/type/customer_type_confirm_delete.html",
        {
            "customer_type": customer_type,
            "capability": get_capability(request.user),
        },
    )


@user_capability_required("can_view_customers")
def customers_view(request):
    """
    View to list and filter customers.
    :param request: HTTP request object
    :return: Rendered customer list page
    """
    search_query = request.GET.get("search", "")
    customer_type_id = request.GET.get("customer_type", "")
    entity_type = request.GET.get("entity_type", "")
    donation_exemption = request.GET.get("donation_exemption", "")
    sort = request.GET.get("sort", "last_name")  # Par défaut, tri par nom
    direction = request.GET.get("direction", "asc")  # Par défaut, ordre ascendant

    order_by = sort

    if direction == "desc":
        order_by = f"-{order_by}"

    filters = {}

    if customer_type_id not in ["", None]:
        filters["customer_type_id"] = customer_type_id
    if entity_type in ["physical", "legal"]:
        filters["customer_type__entity_type"] = entity_type
    if donation_exemption == "true":
        filters_q = Q(donation_exemption=True) | Q(
            customer_type__donation_exemption=True
        )
    elif donation_exemption == "false":
        filters_q = Q(donation_exemption=False) & Q(
            customer_type__donation_exemption=False
        )
    else:
        filters_q = None
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
    if filters_q is not None:
        customers = customers.filter(filters_q)

    current_year = datetime.now().year
    for customer in customers:
        customer.is_membership_up_to_date = (
            customer.is_exempted_from_donation()
            or customer.get_has_paid_membership_fee(current_year)
        )

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
    return render(request, "ui/customers/customer_list.html", context)


@user_capability_required("can_view_customers")
def customer_detail(request, pk):
    """
    Display detailed information about a customer.
    :param request: HTTP request object
    :param pk: Primary key of the customer
    :return: Rendered customer detail page
    """
    customer = get_object_or_404(Customer, pk=pk)

    # Récupérer les réservations du client
    reservations = customer.reservations.all().order_by("-checkout_date")

    # Récupérer les dons du client
    donations = customer.donations.all().order_by("-date")

    # Calculer les statistiques
    total_donations = customer.get_total_donation_amount()
    total_reservations = reservations.count()
    current_year = datetime.now().year
    is_membership_up_to_date = customer.get_has_paid_membership_fee(current_year)

    context = {
        "customer": customer,
        "reservations": reservations,
        "donations": donations,
        "total_donations": total_donations,
        "total_reservations": total_reservations,
        "capability": get_capability(request.user),
        "is_membership_up_to_date": is_membership_up_to_date,
    }
    return render(request, "ui/customers/customer_details.html", context)


@user_capability_required("can_add_customers")
def customer_create(request):
    """
    Create a new customer.
    :param request: HTTP request object
    :return: Rendered customer creation form or redirect on success
    """
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
            "customer_types": CustomerType.objects.all().order_by("name"),
        },
    )


@user_capability_required("can_edit_customers")
def customer_update(request, pk):
    """
    Update an existing customer.
    :param request: HTTP request object
    :param pk: Primary key of the customer to update
    :return: Rendered customer update form or redirect on success
    """
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
            "customer_types": CustomerType.objects.all().order_by("name"),
        },
    )


@user_capability_required("can_delete_customers")
def customer_delete(request, pk):
    """
    Delete a customer after confirming.
    :param request: HTTP request object
    :param pk: Primary key of the customer to delete
    :return: Rendered confirmation page or redirect on success
    """
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


@user_capability_required("can_view_customers")
def search_customers(request):
    """
    Search customers for AJAX requests (e.g., Select2).
    :param request: HTTP request object
    :return: JSON response with search results
    """
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
            "exempted": c.is_exempted_from_donation(),
            "icon": c.customer_type.icon,
            "color": c.customer_type.color,
            "type_name": c.customer_type.name if c.customer_type else "",
        }
        for c in customers
    ]

    return JsonResponse({"results": results, "has_more": has_more})
