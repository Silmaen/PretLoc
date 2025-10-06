"""
Models for managing donations.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ui.customer.models import Customer
from ui.reservation.models import Reservation


class Donation(models.Model):
    """
    Model representing a donation made by a customer.
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="donations",
        verbose_name=_("Client"),
    )
    date = models.DateField(auto_now_add=True, verbose_name=_("Date du don"))
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Montant")
    )
    includes_membership = models.BooleanField(
        default=False, verbose_name=_("Inclut l'adhésion annuelle")
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
        verbose_name=_("Réservation associée"),
    )

    class Meta:
        """
        Meta information for the Donation model.
        """

        verbose_name = _("Don")
        verbose_name_plural = _("Dons")
        ordering = ["-date"]

    def __str__(self):
        """
        String representation of the Donation instance.
        :return: String combining amount, customer and date
        """
        return _(f"Don de {self.amount}€ par {self.customer} le {self.date}")
