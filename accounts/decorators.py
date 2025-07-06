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


def get_capability(user):
    if not user.is_authenticated:
        return {
            "can_add_articles": False,
            "can_edit_articles": False,
            "can_delete_articles": False,
            "can_view_articles": False,
            "can_add_categories": False,
            "can_edit_categories": False,
            "can_delete_categories": False,
            "can_view_customers": False,
            "can_add_customers": False,
            "can_edit_customers": False,
            "can_delete_customers": False,
            "can_view_categories": False,
            "can_create_reservations": False,
            "can_view_reservations": False,
        }
    return {
        # articles
        "can_add_articles": user.profile.user_type in ["admin"],
        "can_edit_articles": user.profile.user_type in ["admin", "manager"],
        "can_delete_articles": user.profile.user_type == "admin",
        "can_view_articles": user.profile.user_type in ["admin", "manager", "member"],
        # customers
        "can_view_customers": user.profile.user_type in ["admin", "manager"],
        "can_add_customers": user.profile.user_type in ["admin", "manager"],
        "can_edit_customers": user.profile.user_type in ["admin", "manager"],
        "can_delete_customers": user.profile.user_type in ["admin"],
        # categories
        "can_add_categories": user.profile.user_type == "admin",
        "can_edit_categories": user.profile.user_type == "admin",
        "can_delete_categories": user.profile.user_type == "admin",
        "can_view_categories": user.profile.user_type in ["admin", "manager", "member"],
        # reservations
        "can_create_reservations": user.profile.user_type in ["admin", "manager"],
        "can_edit_reservations": user.profile.user_type in ["admin", "manager"],
        "can_view_reservations": user.profile.user_type
                                 in ["admin", "manager", "member"],
    }
