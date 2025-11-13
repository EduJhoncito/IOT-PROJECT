from __future__ import annotations

from typing import Dict, Optional

from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone

from monitoring.models import SensorReading

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - dependencia opcional
    redis = None


class DailyStatsGateway:
    """
    Maneja la obtención de métricas diarias desde Redis, con fallback a la BD.
    """

    cache_key = "igp:dashboard:daily:{date}"

    def __init__(self):
        self.client = None
        if getattr(settings, 'REDIS_URL', None) and redis is not None:
            self.client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1,
            )

    def get_today_snapshot(self) -> Dict[str, float]:
        target_date = timezone.localdate()
        cached = self._read_from_cache(target_date)
        if cached:
            cached['source'] = 'redis'
            return cached

        snapshot = self._compute_from_database(target_date)
        self._write_to_cache(target_date, snapshot)
        snapshot['source'] = 'database'
        return snapshot

    def _read_from_cache(self, day) -> Optional[Dict[str, float]]:
        if not self.client:
            return None
        raw = self.client.hgetall(self.cache_key.format(date=day.isoformat()))
        if not raw:
            return None
        return {key: float(value) for key, value in raw.items()}

    def _write_to_cache(self, day, payload: Dict[str, float]) -> None:
        if not self.client:
            return
        key = self.cache_key.format(date=day.isoformat())
        try:
            self.client.hset(key, mapping={k: v for k, v in payload.items() if isinstance(v, (int, float))})
            self.client.expire(key, 3600)
        except Exception:
            # Si Redis no está disponible no se interrumpe el dashboard.
            pass

    def _compute_from_database(self, target_date) -> Dict[str, float]:
        readings = SensorReading.objects.filter(timestamp__date=target_date)
        aggregates = readings.aggregate(
            pulse_avg=Avg('pulse'),
            pulse_peak=Max('pulse'),
            humidity_avg=Avg('humidity_percent'),
            humidity_peak=Max('humidity_percent'),
            humidity_floor=Min('humidity_percent'),
            hit_events=Count('id', filter=Q(hit=True)),
            inclination_events=Count('id', filter=Q(inclination=True)),
        )
        snapshot = {
            'pulse_avg': round(aggregates.get('pulse_avg') or 0, 2),
            'pulse_peak': aggregates.get('pulse_peak') or 0,
            'humidity_avg': round(aggregates.get('humidity_avg') or 0, 2),
            'humidity_peak': round(aggregates.get('humidity_peak') or 0, 2),
            'humidity_floor': round(aggregates.get('humidity_floor') or 0, 2),
            'hit_events': aggregates.get('hit_events') or 0,
            'inclination_events': aggregates.get('inclination_events') or 0,
            'total_readings': readings.count(),
        }
        return snapshot
