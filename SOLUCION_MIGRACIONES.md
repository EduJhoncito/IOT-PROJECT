# Solución al Problema de Migraciones Inconsistentes

## Problema
El error indica que las migraciones de `admin` se aplicaron antes que las de `users`, pero ahora `admin` depende de `users.0001_initial`.

## Solución: Reiniciar la Base de Datos

Como estás en desarrollo y probablemente no tienes datos importantes, la solución más simple es eliminar la base de datos y empezar de nuevo.

### Opción 1: Eliminar y Recrear (Recomendado para Desarrollo)

1. **Elimina la base de datos SQLite3:**
   ```bash
   # En Windows PowerShell:
   Remove-Item db.sqlite3
   
   # O manualmente elimina el archivo db.sqlite3 de la carpeta del proyecto
   ```

2. **Elimina las migraciones aplicadas (opcional, pero recomendado):**
   ```bash
   # Elimina las carpetas __pycache__ en migrations si existen
   Remove-Item -Recurse -Force users\migrations\__pycache__
   Remove-Item -Recurse -Force core\migrations\__pycache__
   ```

3. **Crea las migraciones:**
   ```bash
   python manage.py makemigrations
   ```

4. **Aplica las migraciones:**
   ```bash
   python manage.py migrate
   ```

5. **Crea un superusuario:**
   ```bash
   python manage.py createsuperuser
   ```

### Opción 2: Usar Migraciones Fake (Si tienes datos importantes)

Si tienes datos que no quieres perder, puedes marcar las migraciones como aplicadas:

```bash
# Marcar la migración de users como aplicada (fake)
python manage.py migrate users 0001 --fake

# Luego aplicar las demás migraciones normalmente
python manage.py migrate
```

## Verificación

Después de aplicar las migraciones, verifica que todo esté correcto:

1. **Verifica las tablas creadas:**
   ```bash
   python manage.py dbshell
   ```
   Luego en SQLite:
   ```sql
   .tables
   ```
   Deberías ver: `users_user`, `core_historicaldata`, `core_realtimedata`, etc.

2. **Accede al admin:**
   - Ve a: http://127.0.0.1:8000/admin/
   - Deberías poder iniciar sesión con el superusuario que creaste

## Modelo User Actualizado

El modelo `User` ahora:
- ✅ Hereda de `AbstractBaseUser` (mínimo necesario para autenticación)
- ✅ Tiene `username` y `password` como campos principales
- ✅ Incluye `created_at` y `updated_at`
- ✅ Tiene campos básicos: `is_active`, `is_staff`, `date_joined`
- ✅ Compatible con el sistema de autenticación de Django

