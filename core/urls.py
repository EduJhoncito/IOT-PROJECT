from django.urls import path

from .views import DashboardView, index, latest_readings, history, ingest, CustomLoginView, custom_logout


urlpatterns = [
    path('', index, name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('login/', CustomLoginView.as_view(), name='custom-login'),
    path('logout/', custom_logout, name='custom-logout'),
    path('api/latest-readings/', latest_readings, name='api-latest'),
    path('api/history/', history, name='api-history'),
    path('api/ingest/', ingest, name='api-ingest'),
]
