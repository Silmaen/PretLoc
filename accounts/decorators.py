from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


def user_capability_required(capability):
    """
    Decorator that checks if the user has a specific capability.
    Capabilities are ordered can_<action>_<what>
    with <action> in [add, edit, delete, view]
    and with priority: delete > edit > add > view
    """

    def decorator(view_func):
        """
        Checks if the user has sufficient capability to access the view.
        :param view_func: The view function to be decorated.
        :return: The wrapped view function.
        """

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            """
            Wrapper function that performs the capability check.
            :param request: The HTTP request object.
            :param args: Positional arguments for the view function.
            :param kwargs: Keyword arguments for the view function.
            :return: The result of the view function if access is granted, otherwise redirects to home with an error message.
            """
            if not request.user.is_authenticated:
                messages.error(
                    request,
                    _("Vous devez être connecté pour accéder à cette page."),
                )
                return redirect("ui:home")

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            capabilities = get_capability(request.user)
            if capabilities.get(capability, False):
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
            "can_view_customers_type": False,
            "can_add_customers_type": False,
            "can_edit_customers_type": False,
            "can_delete_customers_type": False,
            "can_view_categories": False,
            "can_add_reservations": False,
            "can_view_reservations": False,
            "can_view_donations": False,
            "can_add_donations": False,
            "can_edit_donations": False,
            "can_delete_donations": False,
            "can_view_users": False,
            "can_add_users": False,
            "can_edit_users": False,
            "can_delete_users": False,
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
        # customer types
        "can_view_customer_types": user.profile.user_type in ["admin"],
        "can_add_customer_types": user.profile.user_type in ["admin"],
        "can_edit_customer_types": user.profile.user_type in ["admin"],
        "can_delete_customer_types": user.profile.user_type in ["admin"],
        # categories
        "can_add_categories": user.profile.user_type == "admin",
        "can_edit_categories": user.profile.user_type == "admin",
        "can_delete_categories": user.profile.user_type == "admin",
        "can_view_categories": user.profile.user_type in ["admin", "manager", "member"],
        # reservations
        "can_add_reservations": user.profile.user_type in ["admin", "manager"],
        "can_edit_reservations": user.profile.user_type in ["admin", "manager"],
        "can_view_reservations": user.profile.user_type
        in ["admin", "manager", "member"],
        "can_delete_reservations": user.profile.user_type in ["admin", "manager"],
        # donations
        "can_view_donations": user.profile.user_type in ["admin", "manager"],
        "can_add_donations": user.profile.user_type in ["admin", "manager"],
        "can_edit_donations": user.profile.user_type in ["admin", "manager"],
        "can_delete_donations": user.profile.user_type in ["admin", "manager"],
        # users
        "can_view_users": user.profile.user_type in ["admin"],
        "can_add_users": user.profile.user_type in ["admin"],
        "can_edit_users": user.profile.user_type in ["admin"],
        "can_delete_users": user.profile.user_type in ["admin"],
    }
