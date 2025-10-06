"""
Admin configuration for donation models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ui.donation.models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    """
    Admin interface for Donation model.
    """

    list_display = ["customer", "amount", "date", "includes_membership", "reservation"]
    list_filter = ["includes_membership", "date", "customer__customer_type"]
    search_fields = [
        "customer__first_name",
        "customer__last_name",
        "customer__company_name",
    ]
    date_hierarchy = "date"
    readonly_fields = ["date"]
    autocomplete_fields = ["customer", "reservation"]

    fieldsets = (
        (_("Informations principales"), {"fields": ("customer", "amount", "date")}),
        (_("Options"), {"fields": ("includes_membership", "reservation")}),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related to reduce database queries.
        """
        qs = super().get_queryset(request)
        return qs.select_related("customer", "reservation")
