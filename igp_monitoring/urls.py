"""
URL configuration for igp_monitoring project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('users.urls')),
]

# Nota: Django automáticamente sirve archivos estáticos cuando:
# - DEBUG = True
# - django.contrib.staticfiles está en INSTALLED_APPS
# - Los archivos están en STATICFILES_DIRS
# No es necesario agregar configuración manual aquí

