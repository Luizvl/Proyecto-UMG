from django.urls import path
from . import views_web

app_name = 'solicitudes'

urlpatterns = [
    path('aplicar/<int:convocatoria_id>/', views_web.aplicar_convocatoria, name='aplicar'),
    path('mis-solicitudes/', views_web.panel_estudiante, name='panel_estudiante'),
]