from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Category, Asset, Customer, Reservation, ReservationItem, StockEvent


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name",
            "description",
            "stock_quantity",
            "category",
            "replacement_value",
            "rental_value",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "customer_type",
            "first_name",
            "last_name",
            "company_name",
            "legal_rep_first_name",
            "legal_rep_last_name",
            "email",
            "phone",
            "address",
        ]
        widgets = {
            "customer_type": forms.RadioSelect(),
            "address": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "rental_value": _("Don minimum demandé pour l'emprunt de cet article."),
            "replacement_value": _(
                "Valeur exigée si l'article n'est pas rendu ou est rendu dans un état irréparable."
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        customer_type = cleaned_data.get("customer_type")

        if customer_type == "physical":
            if not cleaned_data.get("last_name"):
                self.add_error(
                    "last_name",
                    _("Ce champ est obligatoire pour une personne physique"),
                )
        elif customer_type == "legal":
            if not cleaned_data.get("company_name"):
                self.add_error(
                    "company_name",
                    _("Ce champ est obligatoire pour une personne morale"),
                )
            if not cleaned_data.get("legal_rep_last_name"):
                self.add_error(
                    "legal_rep_last_name",
                    _("Le nom du représentant légal est obligatoire"),
                )

        return cleaned_data


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["customer", "checkout_date", "return_date", "notes"]
        widgets = {
            "checkout_date": forms.DateInput(attrs={"type": "date"}),
            "return_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ReservationItemForm(forms.ModelForm):
    class Meta:
        model = ReservationItem
        fields = ["asset", "quantity_reserved"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher uniquement les articles disponibles
        self.fields["asset"].queryset = Asset.objects.filter(stock_quantity__gt=0)


class StockEventForm(forms.ModelForm):
    class Meta:
        model = StockEvent
        fields = ["asset", "event_type", "quantity", "description", "date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir la date actuelle comme valeur par défaut
        from django.utils import timezone

        if not self.instance.pk:  # Si c'est une nouvelle instance
            self.fields["date"].initial = timezone.now().strftime("%Y-%m-%dT%H:%M")
