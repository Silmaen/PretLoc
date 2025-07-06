from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Category, Asset


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

    actions = ["reset_stock_to_zero"]

    def reset_stock_to_zero(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(request, _(f"{updated} articles ont été remis à zéro."))

    reset_stock_to_zero.short_description = _(
        "Remettre le stock à zéro pour les articles sélectionnés"
    )
