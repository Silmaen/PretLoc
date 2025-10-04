"""
Admin configuration for the stock management application.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Category,
    Asset,
    StockEvent,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """

    list_display = ("name", "description_truncated", "created_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)
    ordering = ("name",)

    def description_truncated(self, obj):
        """
        Truncate the description to 50 characters for display in the admin list view.
        :param obj: Category instance
        :return: Truncated description
        """
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description

    description_truncated.short_description = _("Description")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Asset model.
    """

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


@admin.register(StockEvent)
class StockEventAdmin(admin.ModelAdmin):
    """
    Admin configuration for the StockEvent model.
    """

    list_display = ("date", "asset", "event_type", "quantity", "user")
    list_filter = ("event_type", "date", "asset__category")
    search_fields = ("asset__name", "description", "user__username")
    date_hierarchy = "date"
    raw_id_fields = ("asset",)
    readonly_fields = ("user",)
    fieldsets = (
        (None, {"fields": ("asset", "event_type", "quantity")}),
        (_("Détails"), {"fields": ("description", "date", "user")}),
    )
