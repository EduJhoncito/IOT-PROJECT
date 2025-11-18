# Dashboard IGP · Django

Aplicación web para el Instituto Geofísico del Perú (IGP) que centraliza lecturas simuladas de sensores (vibración, inclinación y humedad) desde 2023 hasta la fecha actual. El dashboard ofrece autenticación básica, métricas diarias (preparadas para obtenerse desde Redis), visualizaciones históricas y una narrativa tipo storytelling para la toma de decisiones.

## Requerimientos cumplidos

- **Autenticación** con usuario fijo `admin` / `admin` (creado mediante comando).
- **Dashboard** con dos capas:
  - **Datos del día** listos para Redis (hoy se calculan desde la base relacional y se cachearán al conectar Redis).
  - **Histórico 2023–hoy** con KPIs, gráficos (barras y líneas) y narrativa descriptiva.
- **Base de datos**: `sqlite3` en desarrollo y PostgreSQL en producción (`DATABASE_URL`).
- **Modelado de sensores**: `SensorPacket` agrupa `seq/ts/alerta` y `SensorSample` almacena cada muestra (`soil_raw/pct`, `tilt`, `vib_pulse/hit`).
- **Frontend** 100% HTML + CSS + JavaScript puro, estilo moderno y responsivo.
- **Datos simulados** generados con un comando (`seed_sensor_data`).
- **Filtros & streaming**: filtros por año/mes/día para la data histórica y sección de streaming (SSE) que simula paquetes cada 5 s antes de conectar Redis.

## Requisitos locales

- Python 3.13+ (`py -3` en Windows).
- Pip con acceso a los paquetes listados en `requirements.txt`.

## Configuración local

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py -3 manage.py migrate
py -3 manage.py ensure_admin_user
py -3 manage.py seed_sensor_data --per-day 8 --samples 2
py -3 manage.py runserver
```

> Credenciales de acceso: **admin / admin**

## Comandos útiles

- `manage.py ensure_admin_user`: garantiza que exista el usuario `admin` con la contraseña solicitada.
- `manage.py seed_sensor_data --per-day 12 --samples 2`: genera paquetes desde 2023 con la cantidad de samples deseada (usar `--force` para regenerar).

## Variables de entorno

Consultar `.env.example`. Las principales son:

| Variable               | Descripción                                                  |
|------------------------|--------------------------------------------------------------|
| `DJANGO_SECRET_KEY`    | Clave secreta para producción.                               |
| `DEBUG`                | `1` en local, `0` en Render.                                 |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos (separados por espacios).                   |
| `DATABASE_URL`         | URL PostgreSQL provista por Render.                          |
| `REDIS_URL`            | URL Redis (opcional por ahora, flujo preparado).             |

## Redis (futuro)

La clase `monitoring.services.redis_gateway.DailyStatsGateway` centraliza la lectura/escritura de métricas diarias. Al definir `REDIS_URL`, las estadísticas del día se recuperarán y almacenarán en Redis sin cambios adicionales en las vistas.

Mientras tanto, el endpoint `GET /stream/` expone un flujo SSE que genera JSON nuevos cada 5 s y alimenta la sección de “Tiempo real” del dashboard.

## Despliegue en Render

1. Crear un servicio web usando el repo (Render detecta `render.yaml`).
2. Render aprovisionará una base PostgreSQL (`igp-dashboard-db`) automáticamente.
3. Configurar variables adicionales (ej. `REDIS_URL` cuando esté disponible).
4. Render ejecutará:
   - `pip install -r requirements.txt`
   - `gunicorn igp_dashboard.wsgi`
5. Tras el primer despliegue, conectarse vía shell de Render para ejecutar:
   ```bash
   python manage.py migrate
   python manage.py ensure_admin_user
   python manage.py seed_sensor_data --per-day 8
   ```

## Estructura principal

```
.
├── igp_dashboard/        # Configuración del proyecto Django
├── monitoring/           # App con modelos, vistas, servicios y comandos
├── templates/            # HTML base, login y dashboard
├── static/               # CSS y JS puro para el frontend
├── management commands   # ensure_admin_user & seed_sensor_data
├── requirements.txt
├── render.yaml
├── Procfile
└── README.md
```

## Próximos pasos sugeridos

- Conectar Redis administrado (Render o externo) y definir `REDIS_URL`.
- Crear pipelines de CI/CD para ejecutar `manage.py check` y pruebas automatizadas.
- Añadir alertas y endpoints API para exponer los KPIs a otros sistemas del IGP.
