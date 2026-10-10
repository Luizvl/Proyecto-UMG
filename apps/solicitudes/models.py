from django.conf import settings
from django.db import models

from apps.convocatorias.models import Convocatoria


class Solicitud(models.Model):
    """
    Entidad de dominio: Solicitud de beca.

    El campo `estado` se gestiona a través del patrón State
    (ver states.py) para no dispersar reglas de transición
    (qué cambios de estado son válidos) en las vistas o servicios.
    """

    PENDIENTE = "PENDIENTE"
    EN_EVALUACION = "EN_EVALUACION"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"

    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (EN_EVALUACION, "En Evaluación"),
        (APROBADA, "Aprobada"),
        (RECHAZADA, "Rechazada"),
    ]

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solicitudes"
    )
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE, related_name="solicitudes")
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)
    motivo_rechazo = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitud"
        verbose_name_plural = "Solicitudes"
        unique_together = ("estudiante", "convocatoria")
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Solicitud #{self.pk} - {self.estudiante} - {self.get_estado_display()}"

    # --- Delegación al patrón State ---
    # El modelo no decide si una transición es válida; delega esa
    # responsabilidad al objeto de estado correspondiente.
    def _get_state(self):
        from .states import obtener_estado
        return obtener_estado(self.estado)

    def iniciar_evaluacion(self):
        self._get_state().iniciar_evaluacion(self)

    def aprobar(self):
        self._get_state().aprobar(self)

    def rechazar(self, motivo: str = ""):
        self._get_state().rechazar(self, motivo)


class HistorialEstado(models.Model):
    """Bitácora de cambios de estado, usada para trazabilidad (HU-14)."""
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name="historial")
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.solicitud_id}: {self.estado_anterior} -> {self.estado_nuevo}"


def ruta_documento(instance, filename):
    return f"solicitudes/{instance.solicitud_id}/{filename}"


class Documento(models.Model):
    """Documento de respaldo cargado a una solicitud (HU-08)."""

    TIPO_DPI = "DPI"
    TIPO_CONSTANCIA = "CONSTANCIA_ESTUDIOS"
    TIPO_NOTAS = "NOTAS"
    TIPO_OTRO = "OTRO"
    TIPOS = [
        (TIPO_DPI, "DPI / Documento de identificación"),
        (TIPO_CONSTANCIA, "Constancia de estudios"),
        (TIPO_NOTAS, "Historial de notas"),
        (TIPO_OTRO, "Otro"),
    ]

    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name="documentos")
    tipo = models.CharField(max_length=25, choices=TIPOS, default=TIPO_OTRO)
    archivo = models.FileField(upload_to=ruta_documento)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def __str__(self):
        return f"{self.get_tipo_display()} - Solicitud #{self.solicitud_id}"
