from django.contrib import admin

from .models import SensorReading


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'pulse', 'hit', 'inclination', 'humidity_percent', 'humidity_raw')
    list_filter = ('hit', 'inclination', 'timestamp')
    search_fields = ('timestamp',)
    ordering = ('-timestamp',)
