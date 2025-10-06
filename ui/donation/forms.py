"""
Forms for managing donations.
"""

from django import forms

from ui.donation.models import Donation


class DonationForm(forms.ModelForm):
    """
    Form for creating and editing donations.
    """

    class Meta:
        """
        Meta information for the DonationForm.
        """

        model = Donation
        fields = ["customer", "amount", "includes_membership", "reservation"]
        widgets = {
            "customer": forms.Select(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "includes_membership": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "reservation": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reservation"].required = False
        self.fields["reservation"].queryset = self.fields[
            "reservation"
        ].queryset.select_related("customer")
