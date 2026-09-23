"""
Patrón de diseño: FACADE (estructural)

Problema que resuelve:
    Crear una solicitud, cargar documentos, iniciar su evaluación o
    decidirla involucra varios pasos y varias entidades (Solicitud,
    Convocatoria, Documento, HistorialEstado). Si cada vista de la
    API implementa esos pasos por su cuenta, la lógica de negocio se
    duplica y se vuelve fácil romperla al modificar una sola vista.

Alternativas consideradas:
    - Poner toda la lógica directamente en las vistas de DRF: rápido
      al inicio, pero mezcla HTTP con reglas de negocio y dificulta
      reutilizar la lógica (por ejemplo, desde un comando de consola
      o una tarea programada).
    - "Fat models" (poner todo en Solicitud.models): funciona para
      reglas simples, pero una solicitud que además debe validar
      cupo de convocatoria y coordinarse con Documento excede la
      responsabilidad de una sola entidad.

Por qué Facade:
    SolicitudService expone una interfaz simple y de alto nivel
    (crear_solicitud, agregar_documento, aprobar, rechazar) que oculta
    la coordinación entre modelos. Las vistas solo llaman al service.

Ventaja para el proyecto:
    Si el Product Owner cambia una regla (ej. "ya no se valida cupo,
    ahora se valida por presupuesto"), el cambio se hace en un solo
    lugar sin tocar las vistas ni los serializers.
"""

from django.core.exceptions import ValidationError

from apps.convocatorias.models import Convocatoria

from .models import Documento, Solicitud


class SolicitudService:
    """Fachada del subsistema de solicitudes."""

    @staticmethod
    def crear_solicitud(estudiante, convocatoria: Convocatoria) -> Solicitud:
        """`estudiante` es una instancia de settings.AUTH_USER_MODEL (apps.usuarios.Usuario)."""
        if not convocatoria.esta_abierta():
            raise ValidationError("La convocatoria no está activa.")

        if Solicitud.objects.filter(estudiante=estudiante, convocatoria=convocatoria).exists():
            raise ValidationError("El estudiante ya tiene una solicitud para esta convocatoria.")

        return Solicitud.objects.create(estudiante=estudiante, convocatoria=convocatoria)

    @staticmethod
    def agregar_documento(solicitud: Solicitud, archivo, tipo: str) -> Documento:
        return Documento.objects.create(solicitud=solicitud, archivo=archivo, tipo=tipo)

    @staticmethod
    def iniciar_evaluacion(solicitud: Solicitud) -> None:
        solicitud.iniciar_evaluacion()

    @staticmethod
    def aprobar(solicitud: Solicitud) -> None:
        solicitud.aprobar()

    @staticmethod
    def rechazar(solicitud: Solicitud, motivo: str = "") -> None:
        solicitud.rechazar(motivo)
