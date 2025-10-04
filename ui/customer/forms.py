"""
Forms for the Customer module.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Customer,
    CustomerType,
)


class CustomerTypeForm(forms.ModelForm):
    """
    Form for creating and updating CustomerType instances.
    """

    class Meta:
        """
        Meta information for the CustomerTypeForm.
        """

        model = CustomerType
        fields = ["name", "code", "description", "entity_type", "color"]
        widgets = {
            "color": forms.TextInput(attrs={"type": "color"}),
        }


class CustomerForm(forms.ModelForm):
    """
    Form for creating and updating Customer instances.
    """

    class Meta:
        """
        Meta information for the CustomerForm.
        """

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
            "donation_exemption",
            "notes",
        ]
        widgets = {
            "customer_type": forms.RadioSelect(),
            "address": forms.TextInput(),
            "notes": forms.Textarea(attrs={"rows": 4, "class": "dark-textarea"}),
        }
        help_texts = {
            "rental_value": _("Don minimum demandé pour l'emprunt de cet article."),
            "replacement_value": _(
                "Valeur exigée si l'article n'est pas rendu ou est rendu dans un état irréparable."
            ),
        }

    def clean(self):
        """
        Custom validation to ensure required fields are filled based on customer type.
        :return: cleaned_data
        """
        cleaned_data = super().clean()
        customer_type = cleaned_data.get("customer_type")

        if customer_type in ["physical", "phys_ext", "member"]:
            if not cleaned_data.get("last_name"):
                self.add_error(
                    "last_name",
                    _("Ce champ est obligatoire."),
                )
        elif customer_type == [
            "legal",
            "legal_ext",
            "asso",
            "asso_ext",
        ]:
            if not cleaned_data.get("company_name"):
                self.add_error(
                    "company_name",
                    _("Ce champ est obligatoire."),
                )
            if not cleaned_data.get("legal_rep_last_name"):
                self.add_error(
                    "legal_rep_last_name",
                    _("Le nom du représentant légal est obligatoire"),
                )

        return cleaned_data
