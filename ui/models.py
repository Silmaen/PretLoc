from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")

    def __str__(self):
        return self.name


class Asset(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(verbose_name=_("Description"))
    stock_quantity = models.PositiveIntegerField(
        default=0, verbose_name=_("Quantité en stock")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name=_("items"),
        verbose_name=_("Catégorie"),
    )
    replacement_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Valeur de remplacement")
    )
    rental_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Valeur de location")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.name
