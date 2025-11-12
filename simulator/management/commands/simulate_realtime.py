import random
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import HistoricalData, RealtimeData


class Command(BaseCommand):
    help = 'Simula datos en tiempo real de sensores IoT para el monitoreo de deslizamientos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=3,
            help='Intervalo en segundos entre cada lectura (default: 3)',
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Duración en segundos (0 = infinito, default: 0)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        duration = options['duration']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Iniciando simulación de sensores IoT (intervalo: {interval}s)'
            )
        )
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                # Simular humedad (0-100%)
                humidity = random.uniform(20.0, 80.0)
                
                # Simular inclinación (10% probabilidad de alerta)
                inclination = random.random() < 0.1
                
                # Simular vibración (15% probabilidad de movimiento)
                vibration = random.random() < 0.15
                
                # Crear registro histórico
                HistoricalData.objects.create(
                    timestamp=timezone.now(),
                    humidity=humidity,
                    inclination=inclination,
                    vibration=vibration
                )
                
                # Actualizar o crear registro en tiempo real
                realtime, created = RealtimeData.objects.get_or_create(
                    pk=1,
                    defaults={
                        'timestamp': timezone.now(),
                        'humidity': humidity,
                        'inclination': inclination,
                        'vibration': vibration
                    }
                )
                
                if not created:
                    realtime.timestamp = timezone.now()
                    realtime.humidity = humidity
                    realtime.inclination = inclination
                    realtime.vibration = vibration
                    realtime.save()
                
                iteration += 1
                status_icon = '⚠️' if (inclination or vibration) else '✅'
                
                self.stdout.write(
                    f'[{iteration}] {status_icon} H:{humidity:.1f}% '
                    f'I:{"ALERTA" if inclination else "OK"} '
                    f'V:{"MOVIMIENTO" if vibration else "OK"}'
                )
                
                # Verificar duración
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nSimulación detenida por el usuario.'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error en la simulación: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSimulación finalizada. Total de registros: {iteration}')
        )

