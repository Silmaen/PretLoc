from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Category, Asset, Customer, Reservation, ReservationItem, StockEvent


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description_truncated", "created_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)
    ordering = ("name",)

    def description_truncated(self, obj):
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description

    description_truncated.short_description = _("Description")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "stock_quantity",
        "rental_value",
        "replacement_value",
        "updated_at",
    )
    list_filter = ("category", "created_at", "updated_at")
    search_fields = ("name", "description", "category__name")
    ordering = ("name",)
    date_hierarchy = "created_at"

    fieldsets = (
        (_("Informations générales"), {"fields": ("name", "description", "category")}),
        (_("Gestion du stock"), {"fields": ("stock_quantity",)}),
        (_("Valeurs"), {"fields": ("replacement_value", "rental_value")}),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("get_full_name", "customer_type", "email", "phone")
    list_filter = ("customer_type",)
    search_fields = (
        "last_name",
        "first_name",
        "company_name",
        "email",
        "phone",
        "address",
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
    )

    def get_full_name(self, obj):
        if obj.customer_type == "physical":
            return f"{obj.last_name} {obj.first_name}"
        else:
            return obj.company_name

    get_full_name.short_description = _("Nom")


class ReservationItemInline(admin.TabularInline):
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
    list_display = (
        "id",
        "customer",
        "status",
        "checkout_date",
        "actual_checkout_date",
        "return_date",
        "actual_return_date",
        "donation_amount",
        "total_expected_donation",
    )
    list_filter = ("status", "checkout_date", "return_date")
    search_fields = (
        "customer__last_name",
        "customer__first_name",
        "customer__company_name",
        "notes",
    )
    readonly_fields = ("total_expected_donation",)
    date_hierarchy = "checkout_date"
    inlines = [ReservationItemInline]

    fieldsets = (
        (_("Client"), {"fields": ("customer",)}),
        (_("Dates prévues"), {"fields": ("checkout_date", "return_date")}),
        (
            _("Dates réelles"),
            {"fields": ("actual_checkout_date", "actual_return_date")},
        ),
        (
            _("Statut et don"),
            {"fields": ("status", "donation_amount", "total_expected_donation")},
        ),
        (_("Notes"), {"fields": ("notes",)}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ["checked_out", "returned", "cancelled"]:
            return self.readonly_fields + ("customer", "checkout_date", "return_date")
        return self.readonly_fields


@admin.register(StockEvent)
class StockEventAdmin(admin.ModelAdmin):
    list_display = ("asset", "event_type", "quantity", "date", "user")
    list_filter = ("event_type", "date", "user")
    search_fields = ("asset__name", "description")
    date_hierarchy = "date"
