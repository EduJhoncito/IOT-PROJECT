from django.urls import path

from .views import DashboardView, SensorStreamView, RealtimeRedisView


app_name = 'monitoring'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('stream/', SensorStreamView.as_view(), name='sensor-stream'),
    path("realtime-redis/", RealtimeRedisView.as_view(), name="realtime-redis"),
]
