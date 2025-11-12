from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado para el IGP.
    Solo incluye username y password como solicitado.
    """
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Nombre de usuario',
        help_text='Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.'
    )
    password = models.CharField(max_length=128, verbose_name='Contraseña')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_staff = models.BooleanField(default=False, verbose_name='Es staff')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

