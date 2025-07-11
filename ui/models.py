from django.contrib.auth import get_user_model
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
        max_digits=10, decimal_places=2, verbose_name=_("Don minimum exigé")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.name


class Customer(models.Model):
    TYPE_CHOICES = (
        ("physical", _("Personne physique")),
        ("legal", _("Personne morale")),
    )

    customer_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="physical",
        verbose_name=_("Type de client"),
    )
    # Personne physique
    first_name = models.CharField(max_length=100, verbose_name=_("Prénom"), blank=True)
    last_name = models.CharField(
        max_length=100, verbose_name=_("Nom de famille"), blank=True
    )
    # Personne morale
    company_name = models.CharField(
        max_length=200, verbose_name=_("Raison sociale"), blank=True
    )
    legal_rep_first_name = models.CharField(
        max_length=100, verbose_name=_("Prénom du représentant"), blank=True
    )
    legal_rep_last_name = models.CharField(
        max_length=100, verbose_name=_("Nom du représentant"), blank=True
    )
    # Commun
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=20, verbose_name=_("Téléphone"), blank=True)
    address = models.TextField(verbose_name=_("Adresse"))

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ["last_name", "company_name"]

    def __str__(self):
        if self.customer_type == "legal":
            return self.company_name
        return f"{self.last_name} {self.first_name}"


class Reservation(models.Model):
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
        verbose_name = _("Réservation")
        verbose_name_plural = _("Réservations")
        ordering = ["-checkout_date", "-created_at"]

    def __str__(self):
        return f"{self.customer} - {self.checkout_date}"

    @property
    def total_expected_donation(self):
        """Calcule le don minimum total attendu pour cette réservation"""
        return sum(item.expected_donation for item in self.items.all())


class ReservationItem(models.Model):
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
        verbose_name = _("Élément de réservation")
        verbose_name_plural = _("Éléments de réservation")
        unique_together = [["reservation", "asset"]]

    def __str__(self):
        return f"{self.asset.name} ({self.quantity_reserved})"

    @property
    def expected_donation(self):
        """Calcule le don minimum attendu pour cet élément"""
        return self.quantity_reserved * self.asset.rental_value


class StockEvent(models.Model):
    """
    Modèle pour tracer les différents événements qui affectent le stock
    (pannes, destructions, acquisitions, ventes...)
    """

    class EventType(models.TextChoices):
        REPAIRABLE_ISSUE = "ISSUE", _("Panne réparable")
        DESTRUCTION = "DESTRUCTION", _("Destruction")
        ACQUISITION = "ACQUISITION", _("Acquisition")
        SALE = "SALE", _("Vente")
        INVENTORY_ADJUSTMENT = "INVENTORY_ADJUSTMENT", _("Ajustement d'inventaire")

    asset = models.ForeignKey(
        "Asset",  # Supposant que votre modèle d'article s'appelle Asset
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
        verbose_name = _("Événement de stock")
        verbose_name_plural = _("Événements de stock")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.asset.name} ({self.date.strftime('%d/%m/%Y')})"
