import itertools
import json
import random
import time
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count, Max, Min, Q
from django.db.models.functions import TruncMonth
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from django.conf import settings
from .models import SensorSample
from .services.redis_gateway import DailyStatsGateway

MONTH_NAMES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "setiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    gateway_class = DailyStatsGateway

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = SensorSample.objects.select_related('packet').filter(packet__timestamp__date__gte=date(2023, 1, 1))
        filters = self._extract_filters()
        historical_qs = self._apply_time_filters(base_qs, filters)
        range_meta = self._range_metadata(historical_qs)
        global_stats = self._global_aggregates(historical_qs)
        trend_windows = self._trend_windows(historical_qs)
        daily_stats = self.gateway_class().get_today_snapshot()

        context.update({
            'daily_stats': daily_stats,
            'daily_insights': self._format_daily_insights(daily_stats),
            'kpi_cards': self._build_kpis(global_stats, trend_windows),
            'storyline': self._build_storyline(global_stats),
            'chart_data': json.dumps(self._build_chart_payload(historical_qs), cls=DjangoJSONEncoder),
            'historical_range': range_meta,
            'last_update': self._last_measurement(global_stats),
            'event_breakdown': self._event_breakdown(global_stats),
            'active_filters': filters,
            'filter_options': self._filter_options(filters),
            'filters_applied': any(filters.values()),
            'filter_description': self._filter_description(filters, range_meta),
            'filter_reset_url': self.request.path,
            'sim_stream_enabled': settings.SIM_STREAM_ENABLED,
        })
        return context

    def _extract_filters(self):
        return {
            'year': self._safe_int(self.request.GET.get('year'), minimum=2000, maximum=2100),
            'month': self._safe_int(self.request.GET.get('month'), minimum=1, maximum=12),
            'day': self._safe_int(self.request.GET.get('day'), minimum=1, maximum=31),
        }

    def _safe_int(self, value, *, minimum, maximum):
        if value in (None, ''):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        if parsed < minimum or parsed > maximum:
            return None
        return parsed

    def _apply_time_filters(self, qs, filters):
        if filters['year']:
            qs = qs.filter(packet__timestamp__year=filters['year'])
        if filters['month']:
            qs = qs.filter(packet__timestamp__month=filters['month'])
        if filters['day']:
            qs = qs.filter(packet__timestamp__day=filters['day'])
        return qs

    def _filter_options(self, filters):
        current_year = timezone.localdate().year
        years = [{'value': y, 'label': y} for y in range(2023, current_year + 1)]

        months = [{'value': m, 'label': MONTH_NAMES.get(m, f"Mes {m}")} for m in range(1, 13)]
        days = [{'value': d, 'label': f"{d:02d}"} for d in range(1, 32)]

        return {
            'years': years,
            'months': months,
            'days': days,
        }

    def _range_metadata(self, qs):
        bounds = qs.aggregate(
            start=Min('packet__timestamp'),
            end=Max('packet__timestamp'),
        )
        return {
            'start': (bounds['start'].date() if bounds['start'] else date(2023, 1, 1)),
            'end': (bounds['end'].date() if bounds['end'] else timezone.localdate()),
        }

    def _filter_description(self, filters, range_meta):
        if not any(filters.values()):
            return f"Histórico completo ({range_meta['start']:%b %Y} - {range_meta['end']:%d %b %Y})"

        parts = []
        if filters['year']:
            parts.append(str(filters['year']))
        if filters['month']:
            parts.append(MONTH_NAMES.get(filters['month'], f"Mes {filters['month']}"))
        if filters['day']:
            parts.append(f"Día {filters['day']:02d}")
        return " · ".join(parts)

    def _format_daily_insights(self, stats):
        total = stats.get('total_readings', 0)
        return [
            {
                'label': 'Pulso promedio',
                'value': f"{stats.get('pulse_avg', 0):.1f}",
                'suffix': 'u',
                'helper': f"Fuente {stats.get('source', 'base de datos')}",
            },
            {
                'label': 'Pulso máximo',
                'value': stats.get('pulse_peak', 0),
                'suffix': 'u',
                'helper': 'Pico del día',
            },
            {
                'label': 'Humedad promedio',
                'value': f"{stats.get('humidity_avg', 0):.1f}",
                'suffix': '%',
                'helper': 'Lecturas calibradas',
            },
            {
                'label': 'Eventos detectados',
                'value': stats.get('hit_events', 0) + stats.get('inclination_events', 0),
                'suffix': '',
                'helper': f"Sobre {total} mediciones",
            },
        ] if total else []

    def _global_aggregates(self, qs):
        if not qs.exists():
            return None
        aggregates = qs.aggregate(
            total_readings=Count('id'),
            avg_pulse=Avg('vib_pulse'),
            avg_humidity=Avg('soil_pct'),
            hit_events=Count('id', filter=Q(vib_hit=True)),
            inclination_events=Count('id', filter=Q(tilt=True)),
            humidity_peak=Max('soil_pct'),
            humidity_floor=Min('soil_pct'),
            pulse_peak=Max('vib_pulse'),
            first_timestamp=Min('packet__timestamp'),
            last_timestamp=Max('packet__timestamp'),
        )
        return aggregates

    def _trend_windows(self, qs):
        today = timezone.localdate()
        recent_start = today - timedelta(days=30)
        previous_start = recent_start - timedelta(days=30)
        recent = qs.filter(packet__timestamp__date__gte=recent_start)
        previous = qs.filter(
            packet__timestamp__date__gte=previous_start,
            packet__timestamp__date__lt=recent_start,
        )
        return {
            'recent': recent.aggregate(
                total_readings=Count('id'),
                hit_events=Count('id', filter=Q(vib_hit=True)),
                inclination_events=Count('id', filter=Q(tilt=True)),
                avg_humidity=Avg('soil_pct'),
            ),
            'previous': previous.aggregate(
                total_readings=Count('id'),
                hit_events=Count('id', filter=Q(vib_hit=True)),
                inclination_events=Count('id', filter=Q(tilt=True)),
                avg_humidity=Avg('soil_pct'),
            ),
        }

    def _build_kpis(self, global_stats, trend_windows):
        if not global_stats:
            return []
        cards = []
        recent = trend_windows['recent']
        previous = trend_windows['previous']

        cards.append(self._compose_card(
            label='Lecturas registradas',
            value=self._format_number(global_stats.get('total_readings', 0)),
            helper=f"Últimos 30 días: {self._format_number(recent.get('total_readings', 0))}",
            suffix='',
            trend=self._trend_text(
                recent.get('total_readings', 0),
                previous.get('total_readings', 0),
            ),
        ))

        cards.append(self._compose_card(
            label='Eventos por golpe',
            value=self._format_number(global_stats.get('hit_events', 0)),
            helper=f"En 30 días: {self._format_number(recent.get('hit_events', 0))}",
            suffix='',
            trend=self._trend_text(
                recent.get('hit_events', 0),
                previous.get('hit_events', 0),
            ),
        ))

        cards.append(self._compose_card(
            label='Alertas de inclinación',
            value=self._format_number(global_stats.get('inclination_events', 0)),
            helper=f"En 30 días: {self._format_number(recent.get('inclination_events', 0))}",
            suffix='',
            trend=self._trend_text(
                recent.get('inclination_events', 0),
                previous.get('inclination_events', 0),
            ),
        ))

        cards.append(self._compose_card(
            label='Humedad promedio',
            value=f"{global_stats.get('avg_humidity') or 0:.1f}",
            helper=f"Últimos 30 días: {recent.get('avg_humidity') or 0:.1f}%",
            suffix='%',
            trend=self._trend_text(
                recent.get('avg_humidity') or 0,
                previous.get('avg_humidity') or 0,
            ),
        ))
        return cards

    def _compose_card(self, label, value, helper, suffix, trend):
        trend_text, trend_class = trend
        return {
            'label': label,
            'value': value,
            'helper': helper,
            'suffix': suffix,
            'trend_text': trend_text,
            'trend_class': trend_class,
        }

    def _trend_text(self, current, previous):
        if not previous:
            if not current:
                return 'Sin variación', 'trend-neutral'
            return '+100% vs período previo', 'trend-up'
        change = ((current - previous) / previous) * 100
        sign = '+' if change >= 0 else ''
        css_class = 'trend-up' if change >= 0 else 'trend-down'
        return f'{sign}{change:.1f}% vs período previo', css_class

    def _build_storyline(self, stats):
        if not stats:
            return []
        total_events = stats.get('hit_events', 0) + stats.get('inclination_events', 0)
        hit_ratio = (stats.get('hit_events', 0) / total_events * 100) if total_events else 0
        inclination_ratio = 100 - hit_ratio if total_events else 0
        days_tracked = 0
        if stats.get('first_timestamp') and stats.get('last_timestamp'):
            days_tracked = (stats['last_timestamp'].date() - stats['first_timestamp'].date()).days + 1
        return [
            f"Se analizaron {self._format_number(stats.get('total_readings', 0))} lecturas en {days_tracked} días monitoreados.",
            f"El {hit_ratio:.1f}% de los eventos están asociados a golpeteos y el {inclination_ratio:.1f}% a inclinaciones.",
            f"La humedad oscila entre {stats.get('humidity_floor') or 0:.1f}% y {stats.get('humidity_peak') or 0:.1f}% con un promedio estable.",
        ]

    def _build_chart_payload(self, qs):
        if not qs.exists():
            return {'monthlyPulse': [], 'humidityTrend': []}
        monthly = (
            qs.annotate(month=TruncMonth('packet__timestamp'))
            .values('month')
            .annotate(
                avg_pulse=Avg('vib_pulse'),
                avg_humidity=Avg('soil_pct'),
            )
            .order_by('month')
        )
        monthly_pulse = [
            {'label': m['month'].strftime('%b %y'), 'avgPulse': round(m['avg_pulse'] or 0, 2)}
            for m in monthly
        ]
        humidity_trend = [
            {'label': m['month'].strftime('%b %y'), 'value': round(m['avg_humidity'] or 0, 2)}
            for m in monthly
        ]
        return {'monthlyPulse': monthly_pulse, 'humidityTrend': humidity_trend}

    def _last_measurement(self, stats):
        if not stats or not stats.get('last_timestamp'):
            return 'Sin registros'
        return timezone.localtime(stats['last_timestamp']).strftime('%d %b %Y · %H:%M')

    def _event_breakdown(self, stats):
        if not stats:
            return []
        hit = stats.get('hit_events', 0)
        inclination = stats.get('inclination_events', 0)
        total = hit + inclination or 1
        return [
            {
                'label': 'Eventos por golpe',
                'value': hit,
                'percent': round(hit / total * 100),
            },
            {
                'label': 'Alertas de inclinación',
                'value': inclination,
                'percent': round(inclination / total * 100),
            },
        ]

    def _format_number(self, value):
        return f"{int(value):,}".replace(',', '.') if value is not None else '0'


class SensorStreamView(LoginRequiredMixin, View):
    stream_interval_seconds = 5

    def get(self, request, *args, **kwargs):
        if not settings.SIM_STREAM_ENABLED:
            return StreamingHttpResponse(
                "data: {\"message\": \"Simulación deshabilitada\"}\n\n",
                content_type='text/event-stream',
            )
        response = StreamingHttpResponse(
            self._event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    def _event_stream(self):
        rng = random.Random()
        seq_counter = itertools.count(start=int(timezone.now().timestamp()))
        try:
            while True:
                payload = self._build_payload(next(seq_counter), rng)
                yield f"data: {json.dumps(payload, cls=DjangoJSONEncoder)}\n\n"
                time.sleep(self.stream_interval_seconds)
        except GeneratorExit:
            return

    def _build_payload(self, seq, rng):
        timestamp = timezone.localtime()
        sample_count = rng.randint(2, 4)
        samples = []
        for sensor_id in range(1, sample_count + 1):
            soil_raw = rng.randint(250, 940)
            soil_pct = round(min(100, max(0, (soil_raw / 1024) * 100 + rng.uniform(-2, 2))), 2)
            tilt = 1 if rng.random() > 0.78 else 0
            vib_hit = 1 if rng.random() > 0.7 else 0
            samples.append({
                'id': sensor_id,
                'soil': {'raw': soil_raw, 'pct': soil_pct},
                'tilt': tilt,
                'vib': {
                    'pulse': rng.randint(60, 1500),
                    'hit': vib_hit,
                },
            })
        payload = {
            'seq': seq,
            'alerta': 1 if any(sample['tilt'] or sample['vib']['hit'] for sample in samples) else 0,
            'ts': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'samples': samples,
        }
        return payload
