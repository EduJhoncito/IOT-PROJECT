# Sistema de Monitoreo IGP - Costa Verde

Sistema de monitoreo y alerta temprana de deslizamientos de tierra en la Costa Verde (Lima, Perú) desarrollado para el **Instituto Geofísico del Perú (IGP)**.

## 🎯 Características

- **Dashboard en tiempo real** con actualización automática cada 3 segundos
- **Monitoreo de sensores IoT**: Humedad del suelo, Inclinación y Vibración
- **Gráficos históricos** de humedad del suelo
- **Sistema de autenticación** con protección de vistas
- **API REST** para consulta de datos históricos y en tiempo real
- **Simulador de datos IoT** para pruebas y desarrollo

## 🛠️ Tecnologías

- **Backend**: Django 5.0+
- **Base de datos**: PostgreSQL (Render)
- **Frontend**: HTML5, CSS3, JavaScript puro
- **Gráficos**: Chart.js
- **Deployment**: Render (configurado)

## 📋 Requisitos Previos

- Python 3.10+
- PostgreSQL (local o en Render)
- pip

## 🚀 Instalación Local

1. **Clonar el repositorio** (o descargar los archivos)

2. **Crear entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:
Crear un archivo `.env` en la raíz del proyecto:
```env
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
DATABASE_URL=postgresql://usuario:password@localhost:5432/igp_monitoring
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. **Ejecutar migraciones**:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Crear superusuario**:
```bash
python manage.py createsuperuser
```

7. **Ejecutar servidor de desarrollo**:
```bash
python manage.py runserver
```

8. **Acceder a la aplicación**:
- Login: http://localhost:8000/login/
- Dashboard: http://localhost:8000/dashboard/
- Admin: http://localhost:8000/admin/

## 📊 Simulador de Datos IoT

Para simular datos de sensores en tiempo real:

```bash
python manage.py simulate_realtime
```

Opciones disponibles:
- `--interval N`: Intervalo en segundos entre lecturas (default: 3)
- `--duration N`: Duración en segundos (0 = infinito, default: 0)

Ejemplo:
```bash
python manage.py simulate_realtime --interval 5 --duration 300
```

## 🌐 Despliegue en Render

### Configuración de Base de Datos

1. Crear una base de datos PostgreSQL en Render
2. Obtener la URL de conexión (DATABASE_URL)

### Variables de Entorno en Render

Configurar las siguientes variables en el panel de Render:

```
SECRET_KEY=tu-secret-key-segura-aqui
DEBUG=False
DATABASE_URL=postgresql://usuario:password@host:5432/database
ALLOWED_HOSTS=tu-app.onrender.com
```

### Archivos de Configuración

El proyecto incluye:
- `Procfile`: Configuración para Render
- `requirements.txt`: Dependencias del proyecto
- `settings.py`: Configurado para usar variables de entorno

### Build Command (Render)

```
pip install -r requirements.txt
```

### Start Command (Render)

El `Procfile` ya está configurado, pero puedes usar:
```
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn igp_monitoring.wsgi:application
```

## 📁 Estructura del Proyecto

```
IOT-PROJECT/
├── core/                    # App principal (modelos, vistas, API)
│   ├── models.py           # HistoricalData, RealtimeData
│   ├── views.py            # Dashboard y endpoints API
│   └── urls.py
├── users/                   # App de autenticación
│   ├── models.py           # User personalizado
│   └── views.py            # Login
├── simulator/               # App de simulación
│   └── management/commands/
│       └── simulate_realtime.py
├── templates/               # Plantillas HTML
│   ├── base.html
│   ├── users/login.html
│   └── core/dashboard.html
├── static/                  # Archivos estáticos
│   ├── css/main.css
│   └── js/dashboard.js
├── igp_monitoring/          # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── Procfile
└── README.md
```

## 🔌 Endpoints API

### GET `/api/historical/`
Obtiene los últimos 100 registros históricos.

**Parámetros opcionales:**
- `limit`: Número de registros (default: 100)

**Respuesta:**
```json
{
  "data": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "humidity": 45.5,
      "inclination": 0,
      "vibration": 1
    }
  ]
}
```

### GET `/api/realtime/`
Obtiene el último registro en tiempo real y estadísticas del día.

**Respuesta:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "humidity": 45.5,
  "inclination": 0,
  "vibration": 1,
  "stats": {
    "avg_humidity_today": 42.3,
    "alert_percentage_today": 15.5
  }
}
```

## 🔐 Autenticación

- **Login**: `/login/`
- **Dashboard**: `/dashboard/` (requiere autenticación)
- **Logout**: `/logout/`

Las vistas protegidas redirigen automáticamente a `/login/` si el usuario no está autenticado.

## 📝 Modelos de Datos

### HistoricalData
Almacena registros históricos de sensores:
- `timestamp`: Fecha y hora
- `humidity`: Humedad del suelo (%)
- `inclination`: Inclinación (0=estable, 1=alerta)
- `vibration`: Vibración (0=sin movimiento, 1=movimiento)

### RealtimeData
Almacena el último valor recibido (caché):
- Mismos campos que HistoricalData
- Se actualiza con cada nueva lectura

### User
Modelo de usuario personalizado heredando de `AbstractUser`.

## 🎨 Características del Dashboard

- **Gráfico de humedad** histórico actualizado en tiempo real
- **Indicadores visuales** de inclinación y vibración
- **Métricas del día**: Promedio de humedad, porcentaje de tiempo en alerta
- **Última lectura** recibida con timestamp
- **Diseño responsive** y profesional

## 📞 Soporte

Para más información, contactar al equipo de desarrollo del IGP.

---

**Desarrollado para el Instituto Geofísico del Perú (IGP)**

