from django.contrib import admin

from .models import SensorPacket, SensorSample


class SensorSampleInline(admin.TabularInline):
    model = SensorSample
    extra = 0
    fields = ('sample_id', 'soil_raw', 'soil_pct', 'tilt', 'vib_pulse', 'vib_hit')


@admin.register(SensorPacket)
class SensorPacketAdmin(admin.ModelAdmin):
    list_display = ('seq', 'timestamp', 'alerta', 'samples_count')
    list_filter = ('alerta', 'timestamp')
    search_fields = ('seq',)
    ordering = ('-timestamp',)
    inlines = [SensorSampleInline]

    def samples_count(self, obj):
        return obj.samples.count()


@admin.register(SensorSample)
class SensorSampleAdmin(admin.ModelAdmin):
    list_display = ('packet', 'sample_id', 'soil_pct', 'tilt', 'vib_pulse', 'vib_hit')
    list_filter = ('tilt', 'vib_hit')
    search_fields = ('packet__seq',)
