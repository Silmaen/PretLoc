"""
Admin configuration for reservation models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Customer,
    CustomerType,
)


@admin.register(CustomerType)
class CustomerTypeAdmin(admin.ModelAdmin):
    """
    Admin configuration for the CustomerType model.
    """

    list_display = (
        "name",
        "code",
        "entity_type",
        "color",
        "donation_exemption",
        "donation_coefficient",
        "reservation_period_days",
    )
    list_filter = ("entity_type", "donation_exemption")
    search_fields = ("name", "code", "description")
    ordering = ("name",)

    fieldsets = (
        (_("Informations"), {"fields": ("name", "code", "description")}),
        (_("Classification"), {"fields": ("entity_type", "color")}),
        (
            _("Paramètres de don"),
            {"fields": ("donation_exemption", "donation_coefficient")},
        ),
        (_("Réservation"), {"fields": ("reservation_period_days",)}),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Customer model.
    """

    list_display = (
        "get_name",
        "customer_type",
        "get_entity_type",
        "email",
        "phone",
        "donation_exemption",
        "get_donation_coefficient",
    )
    list_filter = ("customer_type__entity_type", "customer_type", "donation_exemption")
    search_fields = (
        "last_name",
        "first_name",
        "company_name",
        "email",
        "phone",
        "address",
        "customer_type__name",
    )
    ordering = ("last_name", "company_name")

    fieldsets = (
        (_("Type de client"), {"fields": ("customer_type",)}),
        (
            _("Personne physique"),
            {
                "fields": ("first_name", "last_name"),
                "classes": ("collapse",),
                "description": _("Informations pour une personne physique"),
            },
        ),
        (
            _("Personne morale"),
            {
                "fields": (
                    "company_name",
                    "legal_rep_first_name",
                    "legal_rep_last_name",
                ),
                "classes": ("collapse",),
                "description": _("Informations pour une personne morale"),
            },
        ),
        (_("Coordonnées"), {"fields": ("email", "phone", "address")}),
        (
            _("Options"),
            {"fields": ("donation_exemption", "donation_coefficient", "notes")},
        ),
    )

    def get_name(self, obj):
        """
        Display the name of the customer, prioritizing company name if available.
        :param obj: Customer instance
        :return: Name string
        """
        return str(obj)

    get_name.short_description = _("Nom")

    def get_entity_type(self, obj):
        """
        Display the entity type of the customer.
        :param obj: Customer instance
        :return: Entity type string
        """
        return obj.customer_type.det_entity_type_display() if obj.customer_type else ""

    get_entity_type.short_description = _("Type d'entité")

    def get_donation_coefficient(self, obj):
        """
        Display the donation coefficient of the customer.
        :param obj: Customer instance
        :return: Donation coefficient
        """
        return obj.get_donation_coefficient()

    get_donation_coefficient.short_description = _("Coefficient de don")
