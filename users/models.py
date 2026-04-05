from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """
    Custom manager that wraps Django's UserManager.
    Overrides create_superuser to auto-assign admin role.
    """

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    ADMIN = 'admin'
    ANALYST = 'analyst'
    VIEWER = 'viewer'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (ANALYST, 'Analyst'),
        (VIEWER, 'Viewer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=VIEWER)

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def save(self, *args, **kwargs):
        # Admins automatically get Django staff/superuser access for admin panel
        if self.role == self.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Deactivate user without removing from DB."""
        self.is_active = False
        self.save(update_fields=['is_active'])

    @property
    def is_admin_role(self):
        return self.role == self.ADMIN

    @property
    def is_analyst_role(self):
        return self.role == self.ANALYST

    @property
    def is_viewer_role(self):
        return self.role == self.VIEWER

    def __str__(self):
        return f'{self.username} ({self.role})'
