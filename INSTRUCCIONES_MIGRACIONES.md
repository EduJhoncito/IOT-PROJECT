# Instrucciones para Crear las Migraciones

## Problema
Las migraciones no se crearon automáticamente porque faltaban las carpetas `migrations/` en las apps.

## Solución

He creado las carpetas de migraciones y las migraciones iniciales. Ahora necesitas:

### 1. Aplicar las migraciones

Ejecuta en tu terminal:

```bash
python manage.py migrate
```

Esto creará todas las tablas en la base de datos SQLite3:
- `users_user` - Tabla de usuarios
- `core_historicaldata` - Tabla de datos históricos
- `core_realtimedata` - Tabla de datos en tiempo real
- Y todas las tablas del sistema de Django (auth, sessions, etc.)

### 2. Verificar que las tablas se crearon

Puedes verificar en el admin de Django:
- Ve a: http://127.0.0.1:8000/admin/
- Deberías ver:
  - **Core**: Datos Históricos, Datos en Tiempo Real
  - **Users**: Usuarios

### 3. Crear un superusuario (si aún no lo has hecho)

```bash
python manage.py createsuperuser
```

Sigue las instrucciones para crear un usuario con:
- **Username**: (el nombre de usuario que quieras)
- **Password**: (la contraseña que quieras)
- **Email**: (opcional)

## Sobre el Modelo User

El modelo `User` hereda de `AbstractUser`, que **ya incluye automáticamente**:
- ✅ `username` - Nombre de usuario (requerido, único)
- ✅ `password` - Contraseña (se almacena hasheada)
- ✅ `email` - Correo electrónico
- ✅ `first_name`, `last_name` - Nombres
- ✅ `is_active`, `is_staff`, `is_superuser` - Permisos
- ✅ `date_joined` - Fecha de registro
- ✅ Y otros campos estándar de Django

**No necesitas agregar estos campos manualmente** - ya están incluidos por `AbstractUser`.

## Si necesitas regenerar las migraciones

Si por alguna razón necesitas regenerar las migraciones:

```bash
# Eliminar las migraciones existentes (excepto __init__.py)
# Luego ejecutar:
python manage.py makemigrations
python manage.py migrate
```

## Verificar la Base de Datos

Puedes verificar que las tablas se crearon correctamente usando:

```bash
python manage.py dbshell
```

Luego en SQLite:
```sql
.tables
```

Deberías ver todas las tablas creadas.

