"""
Patrón de diseño: STATE (comportamiento)

Problema que resuelve:
    El ciclo de vida de una Solicitud (Pendiente -> En Evaluación ->
    Aprobada/Rechazada) tiene reglas distintas de "qué transiciones son
    válidas" en cada momento. Sin este patrón, esas reglas terminan
    como un bloque gigante de if/elif dentro de vistas o servicios,
    difícil de mantener y de probar.

Alternativas consideradas:
    - Un campo `estado` de texto libre validado con if/elif en el
      servicio: simple al inicio, pero crece mal y mezcla
      responsabilidades (validación + persistencia + notificación).
    - Una máquina de estados con librería externa (django-fsm):
      añade una dependencia extra que no se justifica para el
      alcance del MVP.

Por qué State:
    Cada estado es una clase con su propio comportamiento; agregar un
    estado nuevo (ej. "EN_APELACION" en una futura iteración) no
    obliga a tocar los demás, cumpliendo el principio Open/Closed.

Ventaja para el proyecto:
    Las reglas de negocio del flujo de aprobación quedan aisladas,
    documentadas y testeables de forma independiente al resto del
    sistema.
"""

from django.core.exceptions import ValidationError


class TransicionInvalidaError(ValidationError):
    """Se lanza cuando se intenta una transición de estado no permitida."""
    pass


class EstadoSolicitud:
    """Interfaz base del estado. Cada estado concreto sobreescribe
    únicamente las transiciones que le son válidas."""

    nombre = None

    def iniciar_evaluacion(self, solicitud):
        raise TransicionInvalidaError(
            f"No se puede iniciar evaluación desde el estado '{self.nombre}'."
        )

    def aprobar(self, solicitud):
        raise TransicionInvalidaError(
            f"No se puede aprobar una solicitud en estado '{self.nombre}'."
        )

    def rechazar(self, solicitud, motivo=""):
        raise TransicionInvalidaError(
            f"No se puede rechazar una solicitud en estado '{self.nombre}'."
        )

    def _cambiar_estado(self, solicitud, nuevo_estado, comentario=""):
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


class PendienteState(EstadoSolicitud):
    nombre = "PENDIENTE"

    def iniciar_evaluacion(self, solicitud):
        self._cambiar_estado(solicitud, "EN_EVALUACION")


class EnEvaluacionState(EstadoSolicitud):
    nombre = "EN_EVALUACION"

    def aprobar(self, solicitud):
        self._cambiar_estado(solicitud, "APROBADA")

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
    "APROBADA": AprobadaState(),
    "RECHAZADA": RechazadaState(),
}


def obtener_estado(nombre_estado: str) -> EstadoSolicitud:
    """Factory sencillo que devuelve la instancia de estado correspondiente."""
    try:
        return _ESTADOS[nombre_estado]
    except KeyError:
        raise ValueError(f"Estado desconocido: {nombre_estado}")
