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
                return self._read_from_backend_redis() | {"source": "redis"}
            except Exception as e:
                print("REDIS SNAPSHOT ERROR:", e)

        return {"source": "database"}  # evitar fallbacks incorrectos


    # -------------------------------
    # LECTURA REAL DE REDIS
    # -------------------------------
    def _read_from_backend_redis(self):
        sensor_ids = self._discover_sensor_ids()

        humidity = []
        vibration = []
        tilt_events = 0
        hit_events = 0

        for sid in sensor_ids:

            # --- HUMEDAD (LIST) -> cada elemento es JSON {"porcentaje":.., ...}
            h_items = self.client.lrange(self.HUM_HIST.format(id=sid), -200, -1)
            for entry in h_items:
                try:
                    obj = json.loads(entry)
                    pct = obj.get("porcentaje") or obj.get("pct") or None
                    if pct is not None:
                        humidity.append(float(pct))
                except Exception:
                    # fallback: si no es JSON, intentar split por ":" como antes (legacy)
                    try:
                        parts = entry.split(":")
                        if len(parts) == 2:
                            humidity.append(float(parts[1]))
                    except Exception:
                        pass

            # --- VIBRACIÓN (LIST)
            v_items = self.client.lrange(self.VIB_HIST.format(id=sid), -200, -1)
            for entry in v_items:
                # intentar JSON primero
                try:
                    obj = json.loads(entry)
                    # si guardas objetos o formatos distintos, intenta mapear:
                    # si es {"pulse": X} o similar
                    if isinstance(obj, dict) and "pulse" in obj:
                        vibration.append(float(obj["pulse"]))
                        continue
                except Exception:
                    pass
                # fallback: si es "timestamp:value" como antes
                try:
                    parts = entry.split(":")
                    if len(parts) == 2:
                        vibration.append(float(parts[1]))
                except Exception:
                    pass

            # --- INCLINACIÓN (LIST)
            inc_items = self.client.lrange(self.INC_HIST.format(id=sid), -200, -1)
            for entry in inc_items:
                try:
                    obj = json.loads(entry)
                    val = obj.get("estado") if isinstance(obj, dict) else None
                    if val is None:
                        # legacy
                        parts = entry.split(":")
                        if len(parts) == 2 and parts[1].isdigit():
                            tilt_events += int(parts[1])
                    else:
                        tilt_events += int(val)
                except Exception:
                    try:
                        parts = entry.split(":")
                        if len(parts) == 2 and parts[1].isdigit():
                            tilt_events += int(parts[1])
                    except Exception:
                        pass

            # --- STATS VIBRACIÓN (ZSET) -> algunos guardan score=pulse
            try:
                vib_stats = self.client.zrange(self.VIB_STATS.format(id=sid), 0, -1, withscores=True)
                vibration.extend([float(score) for (_, score) in vib_stats if score is not None])
            except Exception:
                pass

        # --- STATS ALERTA (ZSET con JSON) -> agregar conteo de eventos
        try:
            alert_items = self.client.zrange(self.ALERT_STATS, 0, -1)
            for raw in alert_items:
                try:
                    data = json.loads(raw)
                    for s in data.get("payload", {}).get("samples", []):
                        if s.get("tilt") == 1:
                            tilt_events += 1
                        if s.get("vib", {}).get("hit", 0) == 1:
                            hit_events += 1
                except Exception:
                    pass
        except Exception:
            pass

        # --- último paquete guardado explícitamente (mejor fuente para last_ts/seq)
        last_seq = None
        last_ts = None
        try:
            last_raw = self.client.get("sensor:last_packet")
            if last_raw:
                last_obj = json.loads(last_raw)
                last_seq = last_obj.get("seq")
                last_ts = last_obj.get("ts")
        except Exception:
            # fallback a última alerta en zset (si quieres)
            try:
                latest_alert = self.client.zrevrange(self.ALERT_STATS, 0, 0)
                if latest_alert:
                    a = json.loads(latest_alert[0])
                    last_seq = a.get("seq") or a.get("payload", {}).get("seq")
                    last_ts = a.get("timestamp") or a.get("payload", {}).get("ts")
            except Exception:
                pass

        return {
            "pulse_avg": round(sum(vibration) / len(vibration), 2) if vibration else 0,
            "pulse_peak": max(vibration) if vibration else 0,

            "humidity_avg": round(sum(humidity) / len(humidity), 2) if humidity else 0,
            "humidity_peak": max(humidity) if humidity else 0,
            "humidity_floor": min(humidity) if humidity else 0,

            "hit_events": hit_events,
            "inclination_events": tilt_events,
            "total_readings": max(len(humidity), len(vibration)),
            "last_seq": last_seq,
            "last_timestamp": last_ts
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
