from django.urls import path

from .views import DashboardView, index, latest_readings, history, ingest


urlpatterns = [
    path('', index, name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/latest-readings/', latest_readings, name='api-latest'),
    path('api/history/', history, name='api-history'),
    path('api/ingest/', ingest, name='api-ingest'),
]

