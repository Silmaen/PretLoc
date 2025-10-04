"""
Forms for managing stock categories, assets, and stock events.
"""

from django import forms

from .models import (
    Category,
    Asset,
    StockEvent,
)


class CategoryForm(forms.ModelForm):
    """
    Form for creating and updating Category instances.
    """

    class Meta:
        """
        Meta information for the CategoryForm.
        """

        model = Category
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class AssetForm(forms.ModelForm):
    """
    Form for creating and updating Asset instances.
    """

    class Meta:
        """
        Meta information for the AssetForm.
        """

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


class StockEventForm(forms.ModelForm):
    """
    Form for creating and updating StockEvent instances.
    """

    class Meta:
        """
        Meta information for the StockEventForm.
        """

        model = StockEvent
        fields = ["asset", "event_type", "quantity", "description", "date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set default date to current date and time.
        :param args: Args
        :param kwargs: Kwargs
        """
        super().__init__(*args, **kwargs)
        from django.utils import timezone

        if not self.instance.pk:
            self.fields["date"].initial = timezone.now().strftime("%Y-%m-%dT%H:%M")
