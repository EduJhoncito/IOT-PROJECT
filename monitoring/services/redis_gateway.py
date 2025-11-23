from __future__ import annotations
from typing import Dict, Optional
from django.conf import settings
from django.utils import timezone
import json

try:
    import redis
except ImportError:
    redis = None


class DailyStatsGateway:

    HUM_HIST = "sensor:humedad:{id}:historico"
    VIB_HIST = "sensor:vibracion:{id}:historico"
    INC_HIST = "sensor:inclinacion:{id}:historico"
    VIB_STATS = "sensor:vibracion:{id}:stats"
    ALERT_STATS = "sensor:alerta:stats"

    def __init__(self):
        self.client = None
        if getattr(settings, "REDIS_URL", None) and redis is not None:
            try:
                self.client = redis.Redis.from_url(
                    settings.REDIS_URL, decode_responses=True
                )
                self.client.ping()
                print("REDIS Conectado OK")
            except Exception as e:
                print("REDIS ERROR:", e)
                self.client = None

    def get_today_snapshot(self):
        if self.client:
            try:
                return self._read_from_redis() | {"source": "redis"}
            except Exception as e:
                print("REDIS SNAPSHOT ERROR:", e)

        return {"source": "database"}  # evitar fallbacks incorrectos

    # -------------------------------
    # LECTURA REAL DE REDIS
    # -------------------------------
    def _read_from_redis(self):

        sensor_ids = self._discover_sensor_ids()

        humidity = []
        vibration = []
        tilt_events = 0
        hit_events = 0

        for sid in sensor_ids:

            # --- HUMEDAD (LIST)
            for entry in self.client.lrange(self.HUM_HIST.format(id=sid), -200, -1):
                parts = entry.split(":")
                if len(parts) == 2:
                    humidity.append(float(parts[1]))

            # --- VIBRACIÓN (LIST)
            for entry in self.client.lrange(self.VIB_HIST.format(id=sid), -200, -1):
                parts = entry.split(":")
                if len(parts) == 2:
                    vibration.append(float(parts[1]))

            # --- INCLINACIÓN (LIST)
            for entry in self.client.lrange(self.INC_HIST.format(id=sid), -200, -1):
                parts = entry.split(":")
                if len(parts) == 2 and parts[1].isdigit():
                    tilt_events += int(parts[1])

            # --- STATS VIBRACIÓN (ZSET)
            vib_stats = self.client.zrange(self.VIB_STATS.format(id=sid), 0, -1, withscores=True)
            # score = pulse
            vibration.extend([score for (_, score) in vib_stats])

        # --- STATS ALERTA (ZSET con JSON)
        alert_items = self.client.zrange(self.ALERT_STATS, 0, -1)
        for raw in alert_items:
            try:
                data = json.loads(raw)
                for s in data["payload"]["samples"]:
                    if s["tilt"] == 1:
                        tilt_events += 1
                    if s["vib"].get("hit", 0) == 1:
                        hit_events += 1
            except:
                pass

        return {
            "pulse_avg": round(sum(vibration)/len(vibration), 2) if vibration else 0,
            "pulse_peak": max(vibration) if vibration else 0,

            "humidity_avg": round(sum(humidity)/len(humidity), 2) if humidity else 0,
            "humidity_peak": max(humidity) if humidity else 0,
            "humidity_floor": min(humidity) if humidity else 0,

            "hit_events": hit_events,
            "inclination_events": tilt_events,
            "total_readings": max(len(humidity), len(vibration)),
        }

    # detectar sensores disponibles
    def _discover_sensor_ids(self):
        keys = self.client.keys("sensor:humedad:*:historico")
        ids = set()
        for k in keys:
            try:
                ids.add(int(k.split(":")[2]))
            except:
                pass
        return sorted(ids or [1])
# -------------------------------
