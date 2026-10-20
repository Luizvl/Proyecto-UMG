from django.urls import path

from . import views_web
from .views_ai import mejorar_motivo_ia


app_name = "solicitudes"


urlpatterns = [
    path(
        "aplicar/<int:convocatoria_id>/",
        views_web.aplicar_convocatoria,
        name="aplicar",
    ),
    path(
        "mis-solicitudes/",
        views_web.panel_estudiante,
        name="panel_estudiante",
    ),
    path(
        "ia/mejorar-motivo/",
        mejorar_motivo_ia,
        name="mejorar_motivo_ia",
    ),
]