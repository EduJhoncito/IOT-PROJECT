from django.db import models


class SensorReading(models.Model):
    """
    Lecturas unificadas provenientes de sensores de vibración, inclinación y humedad.
    """

    timestamp = models.DateTimeField(db_index=True)
    pulse = models.PositiveIntegerField(help_text="Nivel capturado por el sensor de vibración")
    hit = models.BooleanField(default=False, help_text="Golpe detectado por el sensor de vibración")
    inclination = models.BooleanField(default=False, help_text="Inclinación detectada")
    humidity_percent = models.FloatField(help_text="Humedad relativa calibrada (0-100%)")
    humidity_raw = models.PositiveIntegerField(help_text="Dato crudo del sensor de 0 a 1024")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
        ]

    def __str__(self) -> str:
        return f"Lectura {self.timestamp:%Y-%m-%d %H:%M}"
