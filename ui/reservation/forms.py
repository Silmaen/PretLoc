"""
Forms for managing reservations and reservation items.
"""

from django import forms

from ui.stock.models import Asset
from .models import (
    Reservation,
    ReservationItem,
)


class ReservationForm(forms.ModelForm):
    """
    Form for creating and updating Reservation instances.
    """

    class Meta:
        """
        Meta information for the ReservationForm.
        """

        model = Reservation
        fields = ["customer", "checkout_date", "return_date", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ReservationItemForm(forms.ModelForm):
    """
    Form for creating and updating ReservationItem instances.
    """

    class Meta:
        """
        Meta information for the ReservationItemForm.
        """

        model = ReservationItem
        fields = ["asset", "quantity_reserved"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = Asset.objects.filter(stock_quantity__gt=0)
