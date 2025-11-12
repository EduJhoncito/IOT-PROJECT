from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import models
from .models import HistoricalData, RealtimeData


@login_required
def dashboard(request):
    """Vista del dashboard principal."""
    return render(request, 'core/dashboard.html')


@login_required
@require_http_methods(["GET"])
def api_historical(request):
    """API endpoint para obtener los últimos 100 registros históricos."""
    limit = int(request.GET.get('limit', 100))
    # Ordenar por timestamp ascendente para el gráfico
    data = HistoricalData.objects.all().order_by('timestamp')[:limit]
    
    return JsonResponse({
        'data': [
            {
                'timestamp': item.timestamp.isoformat(),
                'humidity': item.humidity,
                'inclination': int(item.inclination),
                'vibration': int(item.vibration),
            }
            for item in data
        ]
    })


@login_required
@require_http_methods(["GET"])
def api_realtime(request):
    """API endpoint para obtener el último registro en tiempo real."""
    latest = RealtimeData.get_latest()
    
    # Calcular estadísticas del día
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_data = HistoricalData.objects.filter(timestamp__gte=today_start)
    
    if today_data.exists():
        avg_humidity = today_data.aggregate(
            avg=models.Avg('humidity')
        )['avg'] or 0.0
        
        alert_count = today_data.filter(inclination=True).count()
        total_count = today_data.count()
        alert_percentage = (alert_count / total_count * 100) if total_count > 0 else 0.0
    else:
        avg_humidity = 0.0
        alert_percentage = 0.0
    
    return JsonResponse({
        'timestamp': latest.timestamp.isoformat(),
        'humidity': latest.humidity,
        'inclination': int(latest.inclination),
        'vibration': int(latest.vibration),
        'stats': {
            'avg_humidity_today': round(avg_humidity, 2),
            'alert_percentage_today': round(alert_percentage, 2),
        }
    })

