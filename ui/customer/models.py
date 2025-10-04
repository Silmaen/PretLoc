"""
Models for managing customers and customer types.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerType(models.Model):
    """
    Model representing different types of customers.
    """

    ENTITY_TYPE_CHOICES = (
        ("physical", _("Personne physique")),
        ("legal", _("Personne morale")),
    )

    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    entity_type = models.CharField(
        max_length=10, choices=ENTITY_TYPE_CHOICES, verbose_name=_("Type d'entité")
    )
    color = models.CharField(
        max_length=20, default="#3498db", verbose_name=_("Couleur")
    )

    class Meta:
        """
        Meta information for the CustomerType model.
        """

        verbose_name = _("Type de client")
        verbose_name_plural = _("Types de clients")
        ordering = ["name"]

    def __str__(self):
        """
        String representation of the CustomerType instance.
        :return: Name of the customer type
        """
        return self.name


class Customer(models.Model):
    """
    Model representing a customer, which can be either a physical person or a legal entity.
    """

    customer_type = models.ForeignKey(
        CustomerType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="customers",
        verbose_name=_("Type de client"),
    )
    # Physical person
    first_name = models.CharField(max_length=100, verbose_name=_("Prénom"), blank=True)
    last_name = models.CharField(
        max_length=100, verbose_name=_("Nom de famille"), blank=True
    )
    # Legal entity
    company_name = models.CharField(
        max_length=200, verbose_name=_("Raison sociale"), blank=True
    )
    legal_rep_first_name = models.CharField(
        max_length=100, verbose_name=_("Prénom du représentant"), blank=True
    )
    legal_rep_last_name = models.CharField(
        max_length=100, verbose_name=_("Nom du représentant"), blank=True
    )
    # Common
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=20, verbose_name=_("Téléphone"), blank=True)
    address = models.TextField(verbose_name=_("Adresse"))
    donation_exemption = models.BooleanField(
        default=False, verbose_name=_("Exonération de don")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        """
        Meta information for the Customer model.
        """

        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ["last_name", "company_name"]

    def __str__(self):
        """
        String representation of the Customer instance.
        :return: Name of the customer, prioritizing company name if available
        """
        if self.customer_type.entity_type in ["legal"]:
            return self.company_name
        return f"{self.last_name} {self.first_name}"
