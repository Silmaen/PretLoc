"""
Models for managing stock, categories, and stock events.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Model for categorizing stock items.
    """

    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Meta information for the Category model.
        """

        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")

    def __str__(self):
        """
        String representation of the Category instance.
        :return: Name of the category
        """
        return self.name


class Asset(models.Model):
    """
    Model representing a stock item.
    """

    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(verbose_name=_("Description"))
    stock_quantity = models.PositiveIntegerField(
        default=0, verbose_name=_("Quantité en stock")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="assets",
        verbose_name=_("Catégorie"),
    )
    replacement_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Valeur de remplacement")
    )
    rental_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Don minimum exigé")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta information for the Asset model.
        """

        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        """
        String representation of the Asset instance.
        :return: Name of the asset
        """
        return self.name


class StockEvent(models.Model):
    """
    Model representing events that affect stock levels.
    """

    class EventType(models.TextChoices):
        """
        Types of stock events.
        """

        REPAIRABLE_ISSUE = "ISSUE", _("Panne réparable")
        DESTRUCTION = "DESTRUCTION", _("Destruction")
        ACQUISITION = "ACQUISITION", _("Acquisition")
        SALE = "SALE", _("Vente")
        INVENTORY_ADJUSTMENT = "INVENTORY_ADJUSTMENT", _("Ajustement d'inventaire")
        REPARATION = "REPAIR", _("Réparation")

    asset = models.ForeignKey(
        "Asset",
        on_delete=models.CASCADE,
        verbose_name=_("Article"),
    )
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, verbose_name=_("Type d'événement")
    )
    quantity = models.IntegerField(default=1, verbose_name=_("Quantité"))
    date = models.DateTimeField(verbose_name=_("Date"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Utilisateur responsable"),
    )

    class Meta:
        """
        Meta information for the StockEvent model.
        """

        verbose_name = _("Événement de stock")
        verbose_name_plural = _("Événements de stock")
        ordering = ["-date"]

    def __str__(self):
        """
        String representation of the StockEvent instance.
        :return: String summarizing the stock event
        """
        return f"{self.get_event_type_display()} - {self.asset.name} ({self.date.strftime('%d/%m/%Y')})"
