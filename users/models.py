from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modelo de usuario personalizado para el IGP.
    
    Hereda de AbstractUser, que incluye automáticamente:
    - username: Nombre de usuario (requerido, único)
    - password: Contraseña (hasheada)
    - email: Correo electrónico
    - first_name, last_name: Nombres
    - is_active, is_staff, is_superuser: Permisos
    - date_joined: Fecha de registro
    - Y otros campos estándar de Django
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        # Asegurar que username y password son requeridos (ya lo son por AbstractUser)
        # pero lo documentamos explícitamente

