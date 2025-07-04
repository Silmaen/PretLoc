from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import UserProfile


# Définition de UserProfileInline pour intégrer le profil directement dans l'admin des utilisateurs
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _("Profil")
    fields = ("user_type",)


# Extension de l'admin utilisateur de base pour inclure les profils
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_user_type",
        "is_staff",
    )
    list_filter = (
        "profile__user_type",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    search_fields = ("username", "email", "first_name", "last_name")

    def get_user_type(self, obj):
        return obj.profile.get_user_type_display()

    get_user_type.short_description = _("Type d'utilisateur")
    get_user_type.admin_order_field = "profile__user_type"


# Définition d'une classe admin pour UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_type", "email", "is_superuser")
    list_filter = ("user_type", "user__is_superuser", "user__is_active")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = ("user",)

    def email(self, obj):
        return obj.user.email

    email.short_description = _("Email")
    email.admin_order_field = "user__email"

    def is_superuser(self, obj):
        return obj.user.is_superuser

    is_superuser.short_description = _("Superutilisateur")
    is_superuser.admin_order_field = "user__is_superuser"
    is_superuser.boolean = True


# Désenregistrer l'admin utilisateur de base et enregistrer notre version personnalisée
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
