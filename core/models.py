from django.db import models


class Sensor(models.Model):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    humidity_pct = models.FloatField()
    tilt = models.BooleanField()
    vibration = models.BooleanField()
    recorded_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['recorded_at']),
            models.Index(fields=['sensor', 'recorded_at']),
        ]
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.sensor.code} @ {self.recorded_at}"


class RealtimeReading(models.Model):
    sensor = models.OneToOneField(Sensor, on_delete=models.CASCADE, related_name='realtime')
    humidity_pct = models.FloatField()
    tilt = models.BooleanField()
    vibration = models.BooleanField()
    recorded_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.sensor.code} latest @ {self.recorded_at}"

