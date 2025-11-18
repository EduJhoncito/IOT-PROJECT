import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import SensorPacket, SensorSample


class Command(BaseCommand):
    help = "Genera datos simulados de sensores desde 2023 hasta la fecha actual."

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-day',
            type=int,
            default=12,
            help='Número aproximado de paquetes por día (default: 12).',
        )
        parser.add_argument(
            '--samples',
            type=int,
            default=3,
            help='Cantidad de samples por paquete (default: 3).',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reemplaza los datos existentes antes de generar nueva información.',
        )

    def handle(self, *args, **options):
        per_day = options['per_day']
        per_packet_samples = options['samples']
        force = options['force']

        if per_day < 1 or per_packet_samples < 1:
            self.stderr.write(self.style.ERROR('Los parámetros --per-day y --samples deben ser positivos.'))
            return

        if SensorPacket.objects.exists() and not force:
            self.stdout.write(self.style.WARNING(
                'Ya existen paquetes en la base de datos. Usa --force para regenerar los datos.'
            ))
            return

        if force:
            deleted_packets, _ = SensorPacket.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Se eliminaron {deleted_packets} paquetes previos.'))

        tz = timezone.get_default_timezone()
        start_date = timezone.make_aware(datetime(2023, 1, 1), tz)
        end_date = timezone.now()

        total_days = (end_date.date() - start_date.date()).days + 1
        slot_minutes = 1440 // per_day
        rng = random.Random(42)

        seq = 1
        created_packets = 0
        sample_buffer = []

        for day_offset in range(total_days):
            base_day = start_date + timedelta(days=day_offset)
            base_naive = datetime.combine(base_day.date(), time.min)
            base = timezone.make_aware(base_naive, tz)

            for slot in range(per_day):
                timestamp = base + timedelta(
                    minutes=(slot * slot_minutes) + rng.randint(0, max(1, slot_minutes - 1))
                )
                packet = SensorPacket.objects.create(
                    seq=seq,
                    timestamp=timestamp,
                    alerta=rng.random() > 0.85,
                )
                seq += 1
                created_packets += 1

                for sample_id in range(1, per_packet_samples + 1):
                    soil_raw = rng.randint(250, 900)
                    soil_pct = max(
                        0,
                        min(100, round((soil_raw / 1024) * 100 + rng.uniform(-3, 3), 2)),
                    )
                    sample_buffer.append(SensorSample(
                        packet=packet,
                        sample_id=sample_id,
                        soil_raw=soil_raw,
                        soil_pct=soil_pct,
                        tilt=rng.random() > 0.78,
                        vib_pulse=rng.randint(40, 1400),
                        vib_hit=rng.random() > 0.7,
                    ))

                if len(sample_buffer) >= 750:
                    SensorSample.objects.bulk_create(sample_buffer, batch_size=250)
                    sample_buffer.clear()
                    self.stdout.write(f'{created_packets} paquetes procesados...')

        if sample_buffer:
            SensorSample.objects.bulk_create(sample_buffer, batch_size=250)

        self.stdout.write(self.style.SUCCESS(
            f'Datos simulados generados correctamente ({created_packets} paquetes).'
        ))
