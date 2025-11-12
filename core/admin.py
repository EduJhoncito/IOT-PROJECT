from django.contrib import admin
from .models import HistoricalData, RealtimeData


@admin.register(HistoricalData)
class HistoricalDataAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'humidity', 'inclination', 'vibration')
    list_filter = ('timestamp', 'inclination', 'vibration')
    search_fields = ('timestamp',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(RealtimeData)
class RealtimeDataAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'humidity', 'inclination', 'vibration', 'updated_at')
    readonly_fields = ('timestamp', 'updated_at')

