"""
model for managing reservations and reservation items.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ui.customer.models import Customer
from ui.stock.models import Asset


class Reservation(models.Model):
    """
    Model representing a reservation made by a customer.
    """

    STATUS_CHOICES = (
        ("created", _("Créée")),
        ("validated", _("Validée")),
        ("checked_out", _("Sortie")),
        ("returned", _("Rendue")),
        ("cancelled", _("Annulée")),
    )

    checkout_date = models.DateTimeField(verbose_name=_("Date de sortie prévue"))
    return_date = models.DateTimeField(verbose_name=_("Date de retour prévue"))
    actual_checkout_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Date de sortie réelle")
    )
    actual_return_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Date de retour réelle")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created",
        verbose_name=_("Statut"),
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name=_("Client"),
    )
    donation_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name=_("Don effectué")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_reservations",
        verbose_name=_("Créé par"),
    )
    validated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_reservations",
        verbose_name=_("Validé par"),
    )
    cancelled_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_reservations",
        verbose_name=_("Annulé par"),
    )
    checkout_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkedout_reservations",
        verbose_name=_("Sortie par"),
    )
    returned_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="returned_reservations",
        verbose_name=_("Retour par"),
    )

    class Meta:
        """
        Meta information for the Reservation model.
        """

        verbose_name = _("Réservation")
        verbose_name_plural = _("Réservations")
        ordering = ["-checkout_date", "-created_at"]

    def __str__(self):
        """
        String representation of the Reservation instance.
        :return: String combining customer and checkout date
        """
        return f"{self.customer} - {self.checkout_date}"

    @property
    def total_expected_donation(self):
        """
        Compute the total expected donation for the reservation based on reserved items.
        :return: Total expected donation amount
        """
        if self.customer.is_exempted_from_donation():
            return 0
        return Decimal(str(self.customer.get_donation_coefficient())) * sum(
            item.expected_donation for item in self.items.all()
        )

    @property
    def customer_type(self):
        """
        Return the customer type of the reservation's customer.
        :return: CustomerType instance or None
        """
        return self.customer.customer_type

    def get_start_date(self):
        """
        Return the start date of the reservation.
        :return: Start date (actual or planned)
        """
        if self.actual_checkout_date:
            return self.actual_checkout_date
        return self.checkout_date

    def get_return_date(self):
        """
        Return the return date of the reservation, considering actual return if available.
        :return: Return date (actual, planned, or current if overdue)
        """
        if self.actual_return_date:
            return self.actual_return_date
        if self.status == "checked_out":
            if self.return_date < timezone.now():
                return timezone.now()
        return self.return_date


class ReservationItem(models.Model):
    """
    Model representing an item within a reservation.
    """

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Réservation"),
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="reservation_items",
        verbose_name=_("Article"),
    )
    quantity_reserved = models.PositiveIntegerField(
        default=1, verbose_name=_("Quantité réservée")
    )
    quantity_checked_out = models.PositiveIntegerField(
        default=0, verbose_name=_("Quantité sortie")
    )
    quantity_returned = models.PositiveIntegerField(
        default=0, verbose_name=_("Quantité rendue")
    )
    quantity_damaged = models.PositiveIntegerField(
        default=0, verbose_name=_("Quantité en panne")
    )

    class Meta:
        """
        Meta information for the ReservationItem model.
        """

        verbose_name = _("Élément de réservation")
        verbose_name_plural = _("Éléments de réservation")
        unique_together = [["reservation", "asset"]]

    def __str__(self):
        """
        String representation of the ReservationItem instance.
        :return: String combining asset name and reserved quantity
        """
        return f"{self.asset.name} ({self.quantity_reserved})"

    @property
    def expected_donation(self):
        """
        Calculate the expected donation for this reservation item based on the reserved quantity and asset rental value.
        :return: Expected donation amount
        """
        return self.quantity_reserved * self.asset.rental_value
