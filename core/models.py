from django.db import models
from django.utils import timezone


class HistoricalData(models.Model):
    """Almacena registros históricos de sensores IoT."""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    humidity = models.FloatField(verbose_name='Humedad (%)')
    inclination = models.BooleanField(verbose_name='Inclinación (0=estable, 1=alerta)', default=False)
    vibration = models.BooleanField(verbose_name='Vibración (0=sin movimiento, 1=movimiento)', default=False)

    class Meta:
        verbose_name = 'Dato Histórico'
        verbose_name_plural = 'Datos Históricos'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - H:{self.humidity}% I:{self.inclination} V:{self.vibration}"


class RealtimeData(models.Model):
    """Almacena el último valor recibido de sensores (caché en tiempo real)."""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    humidity = models.FloatField(verbose_name='Humedad (%)')
    inclination = models.BooleanField(verbose_name='Inclinación (0=estable, 1=alerta)', default=False)
    vibration = models.BooleanField(verbose_name='Vibración (0=sin movimiento, 1=movimiento)', default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dato en Tiempo Real'
        verbose_name_plural = 'Datos en Tiempo Real'

    def __str__(self):
        return f"Tiempo Real - H:{self.humidity}% I:{self.inclination} V:{self.vibration}"

    @classmethod
    def get_latest(cls):
        """Obtiene el último registro o crea uno por defecto."""
        return cls.objects.first() or cls.objects.create(
            humidity=0.0,
            inclination=False,
            vibration=False
        )

