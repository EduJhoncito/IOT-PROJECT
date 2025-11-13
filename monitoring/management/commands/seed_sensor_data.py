import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import SensorReading


class Command(BaseCommand):
    help = "Genera datos simulados de sensores desde 2023 hasta la fecha actual."

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-day',
            type=int,
            default=12,
            help='Número aproximado de lecturas por día (default: 12).',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reemplaza los datos existentes antes de generar nueva información.',
        )

    def handle(self, *args, **options):
        per_day = options['per_day']
        force = options['force']

        if per_day < 1:
            self.stderr.write(self.style.ERROR('El parámetro --per-day debe ser positivo.'))
            return

        if SensorReading.objects.exists() and not force:
            self.stdout.write(self.style.WARNING(
                'Ya existen lecturas en la base de datos. Usa --force para regenerar los datos.'
            ))
            return

        if force:
            deleted, _ = SensorReading.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Se eliminaron {deleted} lecturas previas.'))

        tz = timezone.get_default_timezone()
        start_date = timezone.make_aware(datetime(2023, 1, 1), tz)
        end_date = timezone.now()

        total_days = (end_date.date() - start_date.date()).days + 1
        slot_minutes = 1440 // per_day
        rng = random.Random(42)

        batch, created_total = [], 0
        for day_offset in range(total_days):
            base_day = start_date + timedelta(days=day_offset)
            base_naive = datetime.combine(base_day.date(), time.min)
            base = timezone.make_aware(base_naive, tz)

            for slot in range(per_day):
                timestamp = base + timedelta(
                    minutes=(slot * slot_minutes) + rng.randint(0, max(1, slot_minutes - 1))
                )
                humidity_raw = rng.randint(300, 900)
                humidity_percent = max(
                    0,
                    min(100, round((humidity_raw / 1024) * 100 + rng.uniform(-3, 3), 2)),
                )
                batch.append(SensorReading(
                    timestamp=timestamp,
                    pulse=rng.randint(40, 130),
                    hit=rng.random() > 0.75,
                    inclination=rng.random() > 0.8,
                    humidity_percent=humidity_percent,
                    humidity_raw=humidity_raw,
                ))

            if len(batch) >= 750:
                SensorReading.objects.bulk_create(batch, batch_size=250)
                created_total += len(batch)
                batch.clear()
                self.stdout.write(f'{created_total} lecturas generadas...')

        if batch:
            SensorReading.objects.bulk_create(batch, batch_size=250)
            created_total += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Datos simulados generados correctamente ({created_total} lecturas).'
        ))
