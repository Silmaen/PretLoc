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
