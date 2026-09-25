from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CASHIER = 'cashier', 'Cashier'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER,
        help_text="Designates the user's role in the shop."
    )

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_cashier_role(self) -> bool:
        return self.role == self.Role.CASHIER

    def save(self, *args, **kwargs):
        # Superusers are automatically given the admin role
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        return f"{display} ({self.get_role_display()})"
