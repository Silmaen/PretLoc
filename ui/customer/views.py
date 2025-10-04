"""
Views for managing customers and customer types.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _

from accounts.decorators import user_type_required, get_capability
from .forms import (
    CustomerForm,
    CustomerTypeForm,
)
from .models import (
    Customer,
    CustomerType,
)


@login_required
@user_type_required("admin")
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
    return render(request, "ui/customers/customer_type_list.html", context)


@login_required
@user_type_required("admin")
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
        "ui/customers/customer_type_form.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
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
        "ui/customers/customer_type_confirm_delete.html",
        {
            "customer_type": customer_type,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("manager")
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
        filters["donation_exemption"] = True
    elif donation_exemption == "false":
        filters["donation_exemption"] = False
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
        },
    )


@login_required
@user_type_required("manager")
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
        },
    )


@login_required
@user_type_required("manager")
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


@login_required
@user_type_required("manager")
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
            "email": c.email,  # Ajoutez d'autres champs si nécessaire
        }
        for c in customers
    ]

    return JsonResponse({"results": results, "has_more": has_more})
