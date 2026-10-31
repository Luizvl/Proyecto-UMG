"""
Patrón de diseño: STATE (comportamiento)

Problema que resuelve:
    El ciclo de vida de una Solicitud (Pendiente -> En Evaluación ->
    Pendiente Segunda Aprobación -> Aprobada/Rechazada) tiene reglas
    distintas de transiciones válidas en cada momento.

Reglas de Negocio:
    - Flujo normal: PENDIENTE -> EN_EVALUACION -> APROBADA / RECHAZADA
    - Flujo para solicitudes > Q10,000:
      PENDIENTE -> EN_EVALUACION -> PENDIENTE_SEGUNDA_APROBACION -> APROBADA / RECHAZADA

Además, cada cambio de estado:
    - Registra la trazabilidad en HistorialEstado.
    - Genera automáticamente una Notificación para el estudiante.
    - Envía un correo electrónico al estudiante (si tiene correo).
"""

import logging

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction

logger = logging.getLogger(__name__)


class TransicionInvalidaError(ValidationError):
    """Se lanza cuando se intenta una transición de estado no permitida."""
    pass


class EstadoSolicitud:
    """Clase base para los estados de una solicitud."""

    nombre = None

    def iniciar_evaluacion(self, solicitud):
        raise TransicionInvalidaError(
            f"No se puede iniciar evaluación desde el estado '{self.nombre}'."
        )

    def aprobar(self, solicitud):
        raise TransicionInvalidaError(
            f"No se puede aprobar una solicitud en estado '{self.nombre}'."
        )

    def solicitar_segunda_aprobacion(self, solicitud):
        raise TransicionInvalidaError(
            f"No se puede solicitar una segunda aprobación desde el estado '{self.nombre}'."
        )

    def rechazar(self, solicitud, motivo=""):
        raise TransicionInvalidaError(
            f"No se puede rechazar una solicitud en estado '{self.nombre}'."
        )

    def _obtener_nombre_estado(self, estado):
        nombres = {
            "PENDIENTE": "Pendiente",
            "EN_EVALUACION": "En evaluación",
            "PENDIENTE_SEGUNDA_APROBACION": "Pendiente de segunda aprobación",
            "APROBADA": "Aprobada",
            "RECHAZADA": "Rechazada",
        }
        return nombres.get(estado, estado)

    def _programar_correo(self, solicitud, estado_texto, mensaje):
        """
        Envía el correo solo si la transacción se confirma,
        y un fallo de Gmail nunca revierte el cambio de estado.
        """
        correo = solicitud.estudiante.email
        if not correo:
            return

        solicitud_id = solicitud.id
        asunto = f"Solicitud #{solicitud_id}: {estado_texto}"
        cuerpo = (
            f"Hola,\n\n{mensaje}\n\n"
            "Puedes ver el detalle ingresando a la plataforma de becas.\n"
        )

        def enviar():
            try:
                send_mail(asunto, cuerpo, None, [correo], fail_silently=False)
            except Exception:
                logger.exception(
                    "No se pudo enviar el correo de la solicitud #%s",
                    solicitud_id,
                )

        transaction.on_commit(enviar)

    def _crear_notificacion(self, solicitud, estado_anterior, nuevo_estado, comentario=""):
        """Genera una notificación automática para el estudiante."""
        from .models import Notificacion

        estado_anterior_texto = self._obtener_nombre_estado(estado_anterior)
        estado_nuevo_texto = self._obtener_nombre_estado(nuevo_estado)

        if nuevo_estado == "RECHAZADA":
            mensaje = f"Tu solicitud #{solicitud.id} ha sido rechazada."
            if comentario:
                mensaje += f" Motivo: {comentario}"
        elif nuevo_estado == "APROBADA":
            mensaje = f"Tu solicitud #{solicitud.id} ha sido aprobada."
        elif nuevo_estado == "PENDIENTE_SEGUNDA_APROBACION":
            mensaje = (
                f"Tu solicitud #{solicitud.id} recibió la primera aprobación "
                f"y está pendiente de una segunda aprobación."
            )
        elif nuevo_estado == "EN_EVALUACION":
            mensaje = f"Tu solicitud #{solicitud.id} ha pasado a evaluación."
        else:
            mensaje = (
                f"Tu solicitud #{solicitud.id} cambió de "
                f"{estado_anterior_texto} a {estado_nuevo_texto}."
            )

        Notificacion.objects.create(
            destinatario=solicitud.estudiante,
            solicitud=solicitud,
            mensaje=mensaje,
        )

        self._programar_correo(solicitud, estado_nuevo_texto, mensaje)

    def _cambiar_estado(self, solicitud, nuevo_estado, comentario=""):
        """Cambia el estado, registra el historial y dispara la notificación."""
        from .models import HistorialEstado

        estado_anterior = solicitud.estado
        solicitud.estado = nuevo_estado
        solicitud.save(update_fields=["estado", "fecha_actualizacion"])

        HistorialEstado.objects.create(
            solicitud=solicitud,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            comentario=comentario,
        )

        self._crear_notificacion(
            solicitud=solicitud,
            estado_anterior=estado_anterior,
            nuevo_estado=nuevo_estado,
            comentario=comentario,
        )


class PendienteState(EstadoSolicitud):
    nombre = "PENDIENTE"

    def iniciar_evaluacion(self, solicitud):
        self._cambiar_estado(solicitud, "EN_EVALUACION")


class EnEvaluacionState(EstadoSolicitud):
    nombre = "EN_EVALUACION"

    def aprobar(self, solicitud):
        self._cambiar_estado(solicitud, "APROBADA")

    def solicitar_segunda_aprobacion(self, solicitud):
        self._cambiar_estado(
            solicitud,
            "PENDIENTE_SEGUNDA_APROBACION",
            comentario="Solicitud pendiente de segunda aprobación.",
        )

    def rechazar(self, solicitud, motivo=""):
        solicitud.motivo_rechazo = motivo
        solicitud.save(update_fields=["motivo_rechazo"])
        self._cambiar_estado(solicitud, "RECHAZADA", comentario=motivo)


class PendienteSegundaAprobacionState(EstadoSolicitud):
    nombre = "PENDIENTE_SEGUNDA_APROBACION"

    def aprobar(self, solicitud):
        self._cambiar_estado(
            solicitud,
            "APROBADA",
            comentario="Segunda aprobación realizada.",
        )

    def rechazar(self, solicitud, motivo=""):
        solicitud.motivo_rechazo = motivo
        solicitud.save(update_fields=["motivo_rechazo"])
        self._cambiar_estado(solicitud, "RECHAZADA", comentario=motivo)


class AprobadaState(EstadoSolicitud):
    """Estado terminal: no admite más transiciones."""
    nombre = "APROBADA"


class RechazadaState(EstadoSolicitud):
    """Estado terminal: no admite más transiciones."""
    nombre = "RECHAZADA"


_ESTADOS = {
    "PENDIENTE": PendienteState(),
    "EN_EVALUACION": EnEvaluacionState(),
    "PENDIENTE_SEGUNDA_APROBACION": PendienteSegundaAprobacionState(),
    "APROBADA": AprobadaState(),
    "RECHAZADA": RechazadaState(),
}


def obtener_estado(nombre_estado: str) -> EstadoSolicitud:
    """Devuelve el objeto correspondiente al estado actual de la solicitud."""
    try:
        return _ESTADOS[nombre_estado]
    except KeyError:
        raise ValueError(f"Estado desconocido: {nombre_estado}")