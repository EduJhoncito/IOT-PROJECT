from django.db import models


class SensorPacket(models.Model):
    """
    Representa un lote (payload) recibido desde el borde: misma secuencia, timestamp y alerta.
    """

    seq = models.PositiveIntegerField(unique=True, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    alerta = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"Paquete #{self.seq} · {self.timestamp:%Y-%m-%d %H:%M}"


class SensorSample(models.Model):
    """
    Cada sample contiene los valores capturados por los sensores asociados al paquete.
    """

    packet = models.ForeignKey(
        SensorPacket,
        related_name='samples',
        on_delete=models.CASCADE,
    )
    sample_id = models.PositiveIntegerField()
    soil_raw = models.PositiveIntegerField(help_text="Humedad cruda (0-1024)")
    soil_pct = models.FloatField(help_text="Humedad porcentual")
    tilt = models.BooleanField(default=False, help_text="Inclinacion detectada")
    vib_pulse = models.PositiveIntegerField(help_text="Pulso reportado por el sensor de vibracion")
    vib_hit = models.BooleanField(default=False, help_text="Golpe detectado por el sensor de vibracion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-packet__timestamp']
        unique_together = ('packet', 'sample_id')
        indexes = [
            models.Index(fields=['packet', 'sample_id']),
        ]

    def __str__(self) -> str:
        return f"Sample {self.sample_id} del paquete #{self.packet.seq}"
