"""
Admin configuration for the Reservation module.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Reservation,
    ReservationItem,
)


class ReservationItemInline(admin.TabularInline):
    """
    Inline admin interface for ReservationItem model.
    """

    model = ReservationItem
    extra = 1
    fields = [
        "asset",
        "quantity_reserved",
        "quantity_checked_out",
        "quantity_returned",
        "quantity_damaged",
    ]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Reservation model.
    """

    list_display = (
        "customer",
        "status",
        "checkout_date",
        "actual_checkout_date",
        "return_date",
        "actual_return_date",
        "display_total_donations",
        "total_expected_donation",
    )
    list_filter = ("status", "checkout_date", "return_date")
    search_fields = (
        "customer__last_name",
        "customer__first_name",
        "customer__company_name",
        "notes",
    )
    readonly_fields = ("total_expected_donation", "display_total_donations")
    date_hierarchy = "checkout_date"
    inlines = [ReservationItemInline]

    fieldsets = (
        (_("Client"), {"fields": ("customer",)}),
        (
            _("Dates"),
            {
                "fields": (
                    "checkout_date",
                    "return_date",
                    "actual_checkout_date",
                    "actual_return_date",
                    "validated_at",
                    "cancelled_at",
                )
            },
        ),
        (
            _("Statut et don"),
            {
                "fields": (
                    "status",
                    "created_by",
                    "validated_by",
                    "cancelled_by",
                    "checkout_by",
                    "returned_by",
                )
            },
        ),
        (
            _("Dons"),
            {"fields": ("display_total_donations", "total_expected_donation")},
        ),
        (_("Notes"), {"fields": ("notes",)}),
    )

    def display_total_donations(self, obj):
        """
        Display total donations for the reservation.
        :param obj: Reservation instance
        :return: Formatted donation amount
        """
        return f"{obj.total_donations} €"

    display_total_donations.short_description = _("Dons effectués")

    def get_queryset(self, request):
        """
        Optimize queryset with prefetch_related to reduce database queries.
        """
        qs = super().get_queryset(request)
        return qs.prefetch_related("donations")
