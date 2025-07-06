from django import forms

from .models import Category, Asset, Customer


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
