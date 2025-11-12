"""
Script para verificar la configuración de archivos estáticos
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igp_monitoring.settings')

import django
django.setup()

from django.conf import settings

print("=" * 60)
print("VERIFICACIÓN DE CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS")
print("=" * 60)
print(f"\nDEBUG: {settings.DEBUG}")
print(f"STATIC_URL: {settings.STATIC_URL}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"\nSTATICFILES_DIRS:")
for i, static_dir in enumerate(settings.STATICFILES_DIRS, 1):
    print(f"  {i}. {static_dir} (existe: {Path(static_dir).exists()})")

# Verificar archivos CSS
css_file = Path(settings.STATICFILES_DIRS[0]) / 'css' / 'main.css'
print(f"\nArchivo CSS:")
print(f"  Ruta: {css_file}")
print(f"  Existe: {css_file.exists()}")
if css_file.exists():
    print(f"  Tamaño: {css_file.stat().st_size} bytes")

# Verificar archivos JS
js_file = Path(settings.STATICFILES_DIRS[0]) / 'js' / 'dashboard.js'
print(f"\nArchivo JS:")
print(f"  Ruta: {js_file}")
print(f"  Existe: {js_file.exists()}")
if js_file.exists():
    print(f"  Tamaño: {js_file.stat().st_size} bytes")

print("\n" + "=" * 60)
print("Para probar, accede a:")
print(f"  http://127.0.0.1:8000{settings.STATIC_URL}css/main.css")
print("=" * 60)

