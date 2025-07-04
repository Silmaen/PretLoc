from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text=_("Obligatoire. Entrez une adresse email valide."),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        labels = {
            "username": _("Nom d'utilisateur"),
            "email": _("Adresse e-mail"),
            "first_name": _("Prénom"),
            "last_name": _("Nom de famille"),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["user_type"]
        labels = {
            "user_type": _("Type d'utilisateur"),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Désactiver le champ user_type pour les superusers
            if self.instance and self.instance.user.is_superuser:
                self.fields["user_type"].disabled = True
                self.fields["user_type"].help_text = _(
                    "Le statut superutilisateur impose le type Administrateur"
                )
