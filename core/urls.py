from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/historical/', views.api_historical, name='api_historical'),
    path('api/realtime/', views.api_realtime, name='api_realtime'),
]

