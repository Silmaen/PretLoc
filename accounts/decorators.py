from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


def user_type_required(minimum_user_type):
    """
    Décorateur qui vérifie si le type d'utilisateur a un niveau d'accès suffisant.
    La hiérarchie des types est: new < client < member < manager < admin
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Définir l'ordre hiérarchique des types d'utilisateur
            hierarchy = {"new": 0, "client": 1, "member": 2, "manager": 3, "admin": 4}

            # Vérifier si l'utilisateur est connecté
            if not request.user.is_authenticated:
                messages.error(
                    request,
                    _("Vous devez être connecté pour accéder à cette page."),
                )
                return redirect("ui:home")

            # Si c'est un superutilisateur, lui donner toujours accès
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Vérifier le niveau d'accès
            user_level = hierarchy.get(request.user.profile.user_type, -1)
            required_level = hierarchy.get(minimum_user_type, 0)

            if user_level >= required_level:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    _(
                        "Accès refusé. Votre compte ne dispose pas des permissions suffisantes."
                    ),
                )
                return redirect("ui:home")

        return wrapper

    return decorator
