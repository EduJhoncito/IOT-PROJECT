# Generated manually
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Timestamp')),
                ('humidity', models.FloatField(verbose_name='Humedad (%)')),
                ('inclination', models.BooleanField(default=False, verbose_name='Inclinación (0=estable, 1=alerta)')),
                ('vibration', models.BooleanField(default=False, verbose_name='Vibración (0=sin movimiento, 1=movimiento)')),
            ],
            options={
                'verbose_name': 'Dato Histórico',
                'verbose_name_plural': 'Datos Históricos',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='RealtimeData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Timestamp')),
                ('humidity', models.FloatField(verbose_name='Humedad (%)')),
                ('inclination', models.BooleanField(default=False, verbose_name='Inclinación (0=estable, 1=alerta)')),
                ('vibration', models.BooleanField(default=False, verbose_name='Vibración (0=sin movimiento, 1=movimiento)')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Dato en Tiempo Real',
                'verbose_name_plural': 'Datos en Tiempo Real',
            },
        ),
        migrations.AddIndex(
            model_name='historicaldata',
            index=models.Index(fields=['-timestamp'], name='core_histori_timesta_idx'),
        ),
    ]

