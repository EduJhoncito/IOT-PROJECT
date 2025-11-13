import json
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count, Max, Min, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.views.generic import TemplateView

from .models import SensorReading
from .services.redis_gateway import DailyStatsGateway


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    gateway_class = DailyStatsGateway

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        historical_qs = SensorReading.objects.filter(timestamp__date__gte=date(2023, 1, 1))
        global_stats = self._global_aggregates(historical_qs)
        trend_windows = self._trend_windows(historical_qs)
        daily_stats = self.gateway_class().get_today_snapshot()

        context.update({
            'daily_stats': daily_stats,
            'daily_insights': self._format_daily_insights(daily_stats),
            'kpi_cards': self._build_kpis(global_stats, trend_windows),
            'storyline': self._build_storyline(global_stats),
            'chart_data': json.dumps(self._build_chart_payload(historical_qs), cls=DjangoJSONEncoder),
            'historical_range': {
                'start': date(2023, 1, 1),
                'end': timezone.localdate(),
            },
            'last_update': self._last_measurement(global_stats),
            'event_breakdown': self._event_breakdown(global_stats),
        })
        return context

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
            avg_pulse=Avg('pulse'),
            avg_humidity=Avg('humidity_percent'),
            hit_events=Count('id', filter=Q(hit=True)),
            inclination_events=Count('id', filter=Q(inclination=True)),
            humidity_peak=Max('humidity_percent'),
            humidity_floor=Min('humidity_percent'),
            pulse_peak=Max('pulse'),
            first_timestamp=Min('timestamp'),
            last_timestamp=Max('timestamp'),
        )
        return aggregates

    def _trend_windows(self, qs):
        today = timezone.localdate()
        recent_start = today - timedelta(days=30)
        previous_start = recent_start - timedelta(days=30)
        recent = qs.filter(timestamp__date__gte=recent_start)
        previous = qs.filter(
            timestamp__date__gte=previous_start,
            timestamp__date__lt=recent_start,
        )
        return {
            'recent': recent.aggregate(
                total_readings=Count('id'),
                hit_events=Count('id', filter=Q(hit=True)),
                inclination_events=Count('id', filter=Q(inclination=True)),
                avg_humidity=Avg('humidity_percent'),
            ),
            'previous': previous.aggregate(
                total_readings=Count('id'),
                hit_events=Count('id', filter=Q(hit=True)),
                inclination_events=Count('id', filter=Q(inclination=True)),
                avg_humidity=Avg('humidity_percent'),
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
            qs.annotate(month=TruncMonth('timestamp'))
            .values('month')
            .annotate(
                avg_pulse=Avg('pulse'),
                avg_humidity=Avg('humidity_percent'),
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
