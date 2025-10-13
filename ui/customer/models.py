"""
Models for managing customers and customer types.
"""

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.period import Period


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
    donation_exemption = models.BooleanField(
        default=False, verbose_name=_("Exonération de don")
    )
    donation_coefficient = models.FloatField(
        default=1.0, verbose_name=_("Coefficient de don")
    )
    reservation_period_days = models.IntegerField(
        default=360,
        verbose_name=_("Période de réservation (jours avant manifestation)"),
    )

    @property
    def icon(self):
        """
        Get the icon representation for the customer type.
        :return: Icon string
        """
        if self.entity_type == "physical":
            return "fa-user"
        return "fa-building"

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
    donation_coefficient = models.FloatField(
        default=0.0,
        verbose_name=_("Coefficient de don"),
        help_text=_(
            "Coefficient appliqué aux dons effectués par ce client, 0 applique le coefficient pour son type."
        ),
    )

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
        return self.name

    @property
    def name(self):
        """
        Get the full name of the customer.
        :return: Full name string
        """
        if self.customer_type.entity_type in ["legal"]:
            return self.company_name
        return f"{self.last_name} {self.first_name}"

    @property
    def icon(self):
        """
        Get the icon representation for the customer.
        :return: Icon string
        """
        return self.customer_type.icon if self.customer_type else "fa-user"

    @property
    def color(self):
        """
        Get the color associated with the customer type.
        :return: Color string
        """
        return self.customer_type.color if self.customer_type else "#3498db"

    def is_exempted_from_donation(self):
        """
        Check if the customer is exempted from donation.
        :return: True if exempted, False otherwise
        """
        if (
            self.donation_exemption
            or self.customer_type
            and self.customer_type.donation_exemption
        ):
            return True
        return False

    @property
    def donation_exempted(self):
        """
        Property to check if the customer is exempted from donation.
        :return: True if exempted, False otherwise
        """
        return self.is_exempted_from_donation()

    def get_donation_coefficient(self):
        """
        Get the donation coefficient for the customer.
        :return: Donation coefficient
        """
        if self.is_exempted_from_donation():
            return 0.0
        if self.donation_coefficient and self.donation_coefficient > 0:
            return self.donation_coefficient
        if self.customer_type:
            return self.customer_type.donation_coefficient
        return 1.0

    def get_total_donation_amount(self):
        """
        Compute the total donation amount for the customer.
        :return: Total donation amount
        """
        total = sum(donation.amount for donation in self.donations.all())
        return total

    def get_donation_per_year(self, year):
        """
        Compute the total donation amount for the customer in a specific year.
        :param year: Year to filter donations
        :return: Total donation amount for the specified year
        """
        total = sum(
            donation.amount for donation in self.donations.filter(date__year=year)
        )
        return total

    def get_donation_in_period(self, period: Period):
        """
        Compute the total donation amount for the customer in a specific period.
        :param period: Start date of the period
        :return: Total donation amount for the specified period
        """
        total = sum(
            donation.amount
            for donation in self.donations.filter(
                date__gte=period.start_date, date__lte=period.end_date
            )
        )
        return total

    def get_has_paid_membership_fee(self, year):
        """
        Check if the customer has paid the membership fee for a specific year.
        :param year: Year to check membership fee payment
        :return: True if membership fee is paid, False otherwise
        """
        if self.is_exempted_from_donation():
            return True
        membership_fee_donations = self.donations.filter(
            date__year=year, includes_membership=True
        )
        return membership_fee_donations.exists()

    def get_membership_fee(self, year):
        """
        Get the membership fee for a specific year.
        :param year: Year to get the membership fee.
        :return: Membership fee amount
        """
        if self.is_exempted_from_donation():
            return 0.0
        if self.get_has_paid_membership_fee(year):
            return 0.0
        # Fixed membership fee amount (to be set dynamically later)
        membership_donation = Decimal(5.00)
        return membership_donation * Decimal(str(self.get_donation_coefficient()))
