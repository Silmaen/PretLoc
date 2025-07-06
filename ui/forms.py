from django import forms

from .models import Category, Asset


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
