import json
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from .models import Sensor, RealtimeReading, SensorReading, AppUser
import os
from .auth import CustomLoginRequiredMixin, get_current_user, login_user, logout_user
from django.db import connections
from django.db.utils import OperationalError


class DashboardView(CustomLoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'


def index(request):
    if get_current_user(request):
        return redirect('dashboard')
    return redirect('custom-login')


def latest_readings(request):
    def fetch_raw(alias):
        try:
            with connections[alias].cursor() as cur:
                cur.execute(
                    "SELECT sensor_id, humidity_pct, tilt, vibration, recorded_at FROM core_realtimereading"
                )
                cols = ['sensor_id', 'humidity_pct', 'tilt', 'vibration', 'recorded_at']
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            return []

    single = os.getenv('SINGLE_DB', 'false').lower() == 'true'
    try_aliases = ['historical'] if single else ['historical', 'cache', 'default']

    rows = []
    for al in try_aliases:
        rows = fetch_raw(al)
        if rows:
            break

    if not rows:
        return JsonResponse({'results': []})

    sensor_ids = [r['sensor_id'] for r in rows]
    sensors = {s.id: s for s in Sensor.objects.using('historical').filter(id__in=sensor_ids)}
    data = []
    for r in rows:
        s = sensors.get(r['sensor_id'])
        code = s.code if s else ''
        name = s.name if s else ''
        data.append({
            'sensor': code,
            'name': name,
            'humidity_pct': float(r['humidity_pct']),
            'tilt': int(r['tilt']),
            'vibration': int(r['vibration']),
            'recorded_at': str(r['recorded_at']),
        })

    return JsonResponse({'results': data})


def _parse_iso8601(value: str):
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        return None


def history(request):
    sensor_code = request.GET.get('sensor')
    if not sensor_code:
        return HttpResponseBadRequest('Missing sensor parameter')

    dt_from = _parse_iso8601(request.GET.get('from', ''))
    dt_to = _parse_iso8601(request.GET.get('to', ''))

    try:
        sensor = Sensor.objects.get(code=sensor_code)
    except Sensor.DoesNotExist:
        return HttpResponseBadRequest('Unknown sensor')

    qs = SensorReading.objects.filter(sensor=sensor)
    if dt_from:
        qs = qs.filter(recorded_at__gte=dt_from)
    if dt_to:
        qs = qs.filter(recorded_at__lte=dt_to)

    results = [
        {
            'recorded_at': r.recorded_at.isoformat(),
            'humidity_pct': r.humidity_pct,
            'tilt': int(bool(r.tilt)),
            'vibration': int(bool(r.vibration)),
        }
        for r in qs.order_by('-recorded_at')[:1000]
    ]
    return JsonResponse({'sensor': sensor.code, 'results': results})


@csrf_exempt
def ingest(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    auth = request.headers.get('Authorization', '')
    token_expected = os.getenv('INGEST_TOKEN', '')
    token = ''
    if auth.startswith('Bearer '):
        token = auth[len('Bearer '):]
    elif auth.startswith('Token '):
        token = auth[len('Token '):]

    if not token_expected or token != token_expected:
        return HttpResponseForbidden('Invalid token')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    code = payload.get('code')
    humidity = payload.get('humidity_pct')
    tilt = payload.get('tilt')
    vibration = payload.get('vibration')
    recorded_at = payload.get('recorded_at')

    if code is None or humidity is None or tilt is None or vibration is None:
        return HttpResponseBadRequest('Missing fields')

    try:
        humidity = float(humidity)
        tilt = bool(int(tilt)) if isinstance(tilt, (int, str)) else bool(tilt)
        vibration = bool(int(vibration)) if isinstance(vibration, (int, str)) else bool(vibration)
    except Exception:
        return HttpResponseBadRequest('Invalid field types')

    dt = _parse_iso8601(recorded_at) if recorded_at else timezone.now()
    if not dt:
        dt = timezone.now()

    sensor, _ = Sensor.objects.get_or_create(code=code, defaults={'name': code})

    # Upsert realtime
    RealtimeReading.objects.update_or_create(
        sensor=sensor,
        defaults={
            'humidity_pct': humidity,
            'tilt': tilt,
            'vibration': vibration,
            'recorded_at': dt,
        },
    )

    # Append to historical
    SensorReading.objects.create(
        sensor=sensor,
        humidity_pct=humidity,
        tilt=tilt,
        vibration=vibration,
        recorded_at=dt,
    )

    return JsonResponse({'status': 'ok'})


class CustomLoginView(TemplateView):
    template_name = 'core/custom_login.html'

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.GET.get('next') or '/dashboard/'

        try:
            user = AppUser.objects.using('historical').get(username=username, is_active=True)
        except AppUser.DoesNotExist:
            return self.render_to_response({'error': 'Usuario o contraseña incorrectos.'})

        if not user.check_password(password):
            return self.render_to_response({'error': 'Usuario o contraseña incorrectos.'})

        login_user(request, user)
        return redirect(next_url)


def custom_logout(request):
    logout_user(request)
    return redirect('custom-login')
