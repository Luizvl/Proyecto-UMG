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
    PENDIENTE_SEGUNDA_APROBACION = "PENDIENTE_SEGUNDA_APROBACION"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"

    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (EN_EVALUACION, "En Evaluación"),
        (PENDIENTE_SEGUNDA_APROBACION, "Pendiente de segunda aprobación"),
        (APROBADA, "Aprobada"),
        (RECHAZADA, "Rechazada"),
    ]

    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solicitudes"
    )
    
    convocatoria = models.ForeignKey(
        Convocatoria, on_delete=models.CASCADE, related_name="solicitudes"
    )
    
    estado = models.CharField(
        max_length=35,
        choices=ESTADOS,
        default=PENDIENTE,
    )

    # --- Campos de Jonathan (Doble aprobación) ---
    monto_solicitado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    primer_aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="solicitudes_primera_aprobacion"
    )
    fecha_primera_aprobacion = models.DateTimeField(null=True, blank=True)
    segundo_aprobador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="solicitudes_segunda_aprobacion"
    )
    fecha_segunda_aprobacion = models.DateTimeField(null=True, blank=True)

    motivo = models.TextField(max_length=1000, default="")
    motivo_rechazo = models.TextField(blank=True)

    # --- Campos de Álvaro (Auditoría y Porcentaje) ---
    porcentaje_aprobado = models.IntegerField(
        "Porcentaje de Beca",
        default=0,
        help_text="Ej: 100 para beca completa, 50 para media beca, 25 para beca parcial."
    )

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
    def _get_state(self):
        from .states import obtener_estado
        return obtener_estado(self.estado)

    def iniciar_evaluacion(self):
        self._get_state().iniciar_evaluacion(self)

    def aprobar(self):
        self._get_state().aprobar(self)

    def solicitar_segunda_aprobacion(self):
        self._get_state().solicitar_segunda_aprobacion(self)

    def rechazar(self, motivo: str = ""):
        self._get_state().rechazar(self, motivo)


class HistorialEstado(models.Model):
    """Bitácora de cambios de estado de una solicitud."""
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name="historial"
    )
    estado_anterior = models.CharField(max_length=35)
    estado_nuevo = models.CharField(max_length=35)
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.solicitud_id}: {self.estado_anterior} -> {self.estado_nuevo}"


class Notificacion(models.Model):
    """
    Notificación generada automáticamente cuando
    cambia el estado de una solicitud. (Implementación Jonathan)
    """
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones"
    )
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name="notificaciones"
    )
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Notificación para {self.destinatario} - Solicitud #{self.solicitud_id}"


def ruta_documento(instance, filename):
    return f"solicitudes/{instance.solicitud_id}/{filename}"


class Documento(models.Model):
    """Documento de respaldo cargado a una solicitud."""
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

    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name="documentos"
    )
    tipo = models.CharField(max_length=25, choices=TIPOS, default=TIPO_OTRO)
    archivo = models.FileField(upload_to=ruta_documento)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def __str__(self):
        return f"{self.get_tipo_display()} - Solicitud #{self.solicitud_id}"


class AuditoriaSolicitud(models.Model):
    """
    Registro de Auditoría (Implementación Álvaro)
    Control de acciones específicas realizadas por administradores.
    """
    solicitud = models.ForeignKey(
        Solicitud, on_delete=models.CASCADE, related_name='historial_auditoria'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    accion = models.CharField(max_length=100)
    resultado = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Bitácora de Auditorías'
        ordering = ['-fecha'] 

    def __str__(self):
        return f"[{self.fecha.strftime('%d/%m/%Y %H:%M')}] {self.accion} por {self.usuario}"