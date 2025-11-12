from django.db import models
from django.contrib.auth.hashers import make_password, check_password


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


class AppUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

    def set_password(self, raw_password: str):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password_hash)
