import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Sensor, SensorReading, RealtimeReading


class Command(BaseCommand):
    help = "Crea sensores demo y genera lecturas históricas + tiempo real"

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='Horas hacia atrás a simular')
        parser.add_argument('--interval', type=int, default=5, help='Minutos entre lecturas')

    def handle(self, *args, **opts):
        hours = opts['hours']
        interval = opts['interval']

        stations = [
            ('SEN01', 'Estación Miraflores'),
            ('SEN02', 'Estación Barranco'),
            ('SEN03', 'Estación Magdalena'),
        ]

        now = timezone.now()
        start = now - timedelta(hours=hours)
        step = timedelta(minutes=interval)

        created_sensors = []
        for code, name in stations:
            s, _ = Sensor.objects.using('historical').get_or_create(code=code, defaults={'name': name})
            created_sensors.append(s)

        # Generar histórico
        for sensor in created_sensors:
            SensorReading.objects.using('historical').filter(sensor=sensor, recorded_at__gte=start).delete()
            t = start
            base = random.uniform(40, 70)
            while t <= now:
                # Humedad con tendencia suave + ruido
                trend = (t - start).total_seconds() / (hours * 3600)
                humidity = max(0, min(100, base + 8 * (trend - 0.5) + random.gauss(0, 2)))
                # Eventos binarios esporádicos
                tilt = 1 if random.random() < 0.015 else 0
                vibration = 1 if random.random() < 0.02 else 0
                SensorReading.objects.using('historical').create(
                    sensor=sensor,
                    humidity_pct=humidity,
                    tilt=tilt,
                    vibration=vibration,
                    recorded_at=t,
                )
                t += step

            # Tiempo real: último punto
            last = SensorReading.objects.using('historical').filter(sensor=sensor).order_by('-recorded_at').first()
            if last:
                RealtimeReading.objects.using('historical').update_or_create(
                    sensor=sensor,
                    defaults={
                        'humidity_pct': last.humidity_pct,
                        'tilt': last.tilt,
                        'vibration': last.vibration,
                        'recorded_at': last.recorded_at,
                    },
                )

        self.stdout.write(self.style.SUCCESS('Datos demo generados.'))

