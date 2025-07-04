from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ("admin", _("Administrateur")),  # Can manage users and settings
        ("manager", _("Gestionnaire")),  # Can create reservations for any customer
        ("member", _("Membre")),  # Can manage stock (add, remove, update items)
        ("client", _("Client")),  # Consult stock availability, consult his reservations
        ("new", _("Nouveau")),  # Newly registered user, need administrator to validate
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="new"
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        if self.user.is_superuser:
            self.user_type = "admin"
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_type = "admin" if instance.is_superuser else "new"
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
