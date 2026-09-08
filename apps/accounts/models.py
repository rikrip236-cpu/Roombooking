from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('admin', 'Administrateur'),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Rôle'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    department = models.CharField(max_length=100, blank=True, verbose_name='Département')
    floor = models.CharField(max_length=20, blank=True, verbose_name='Étage')

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def is_standard_user(self):
        return self.role == 'user' and not self.is_superuser
