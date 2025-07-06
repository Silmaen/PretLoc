from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from .decorators import user_type_required, get_capability
from .forms import SignUpForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile


def is_admin(user):
    return user.is_authenticated and user.profile.user_type == "admin"


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Par défaut, nouvel utilisateur est de type "new".
            user.profile.user_type = "new"
            user.profile.save()

            # Connecter l'utilisateur après inscription
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect("ui:home")
    else:
        form = SignUpForm()
    return render(
        request,
        "accounts/signup.html",
        {
            "form": form,
            "capability": get_capability(request.user),
        },
    )


@login_required
def user_profile(request):
    admin = is_admin(request.user)
    is_superuser = request.user.is_superuser

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if admin and not is_superuser:
            profile_form = ProfileUpdateForm(
                request.POST, instance=request.user.profile
            )
            profile_valid = profile_form.is_valid()
        else:
            profile_form = ProfileUpdateForm(instance=request.user.profile)
            profile_valid = True  # Pour les non-admins, on ne modifie pas le profil

        if user_form.is_valid() and profile_valid:
            user_form.save()
            if admin and not is_superuser:
                profile_form.save()
            messages.success(request, _("Votre profil a été mis à jour avec succès."))
            return redirect("user_profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        # Désactiver le champ pour les non-admins
        if not admin or is_superuser:
            profile_form.fields["user_type"].disabled = True

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "is_admin": admin,
        "is_superuser": is_superuser,
        "capability": get_capability(request.user),
    }
    return render(request, "accounts/profile.html", context)


@login_required
@user_type_required("admin")
def manage_users(request):
    users = UserProfile.objects.all()
    return render(
        request,
        "accounts/manage_users.html",
        {
            "users": users,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def edit_user(request, user_id):
    user_profile_local = UserProfile.objects.get(id=user_id)

    if request.method == "POST":
        # Récupérer les données du formulaire
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        user_type = request.POST.get("user_type")

        # Mettre à jour l'utilisateur
        user = user_profile_local.user
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Mettre à jour le profil
        user_profile_local.user_type = user_type
        user_profile_local.save()

        messages.success(
            request, _("Les informations de l'utilisateur ont été mises à jour.")
        )
        return redirect("accounts:manage_users")

    return render(
        request,
        "accounts/edit_user.html",
        {
            "user_profile": user_profile_local,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def reset_password(request, user_id):
    user_profile_local = UserProfile.objects.get(id=user_id)
    user = user_profile_local.user

    # Empêcher la réinitialisation de son propre mot de passe
    if user.id == request.user.id:
        messages.error(
            request,
            _(
                "Vous ne pouvez pas réinitialiser votre propre mot de passe par cette méthode. Utilisez la page de profil."
            ),
        )
        return redirect("accounts:edit_user", user_id=user_id)

    # Générer un mot de passe aléatoire
    import random
    import string

    temp_password = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(10)
    )

    # Définir le nouveau mot de passe
    user.set_password(temp_password)
    user.save()

    messages.success(
        request,
        _("Le mot de passe de {username} a été réinitialisé à: {password}").format(
            username=user.username, password=temp_password
        ),
    )
    return redirect("accounts:edit_user", user_id=user_id)


@login_required
@user_type_required("admin")
def create_user(request):
    if request.method == "POST":
        # Récupérer les données du formulaire
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        user_type = request.POST.get("user_type")
        password = request.POST.get("password")

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Mettre à jour le profil
        user.profile.user_type = user_type
        user.profile.save()

        messages.success(request, _("L'utilisateur a été créé avec succès."))
        return redirect("accounts:manage_users")

    # Passer les types d'utilisateur au template
    user_types = UserProfile.USER_TYPE_CHOICES
    return render(
        request,
        "accounts/create_user.html",
        {
            "user_types": user_types,
            "capability": get_capability(request.user),
        },
    )


@login_required
@user_type_required("admin")
def delete_user(request, user_id):
    user_profile_local = UserProfile.objects.get(id=user_id)

    # Empêcher la suppression de son propre compte
    if user_profile_local.user.id == request.user.id:
        messages.error(request, _("Vous ne pouvez pas supprimer votre propre compte."))
        return redirect("accounts:manage_users")

    username = user_profile_local.user.username
    # Supprimer l'utilisateur (la suppression du profil se fait automatiquement grâce à CASCADE)
    user_profile_local.user.delete()

    messages.success(
        request, _("L'utilisateur {} a été supprimé avec succès.").format(username)
    )
    return redirect("accounts:manage_users")
