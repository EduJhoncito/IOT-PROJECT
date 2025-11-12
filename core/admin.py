from django.contrib import admin

from .models import Sensor, SensorReading, RealtimeReading


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'location', 'is_active')
    search_fields = ('code', 'name')


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'humidity_pct', 'tilt', 'vibration', 'recorded_at')
    list_filter = ('sensor', 'tilt', 'vibration')
    date_hierarchy = 'recorded_at'


@admin.register(RealtimeReading)
class RealtimeReadingAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'humidity_pct', 'tilt', 'vibration', 'recorded_at')
    list_filter = ('tilt', 'vibration')

