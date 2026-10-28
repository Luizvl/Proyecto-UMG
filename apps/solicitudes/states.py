"""
Patrón de diseño: STATE (comportamiento)

Controla las transiciones válidas de una solicitud de beca.

Además, cada cambio de estado:
- Registra el evento en HistorialEstado.
- Genera una notificación para el estudiante.

Flujo normal:
PENDIENTE -> EN_EVALUACION -> APROBADA / RECHAZADA

Flujo para solicitudes mayores a Q10,000:
PENDIENTE
    -> EN_EVALUACION
    -> PENDIENTE_SEGUNDA_APROBACION
    -> APROBADA / RECHAZADA
"""

from django.core.exceptions import ValidationError


class TransicionInvalidaError(ValidationError):
    """
    Se lanza cuando se intenta realizar una transición
    de estado que no está permitida.
    """

    pass


class EstadoSolicitud:
    """
    Clase base para los estados de una solicitud.
    """

    nombre = None

    def iniciar_evaluacion(
        self,
        solicitud,
    ):
        raise TransicionInvalidaError(
            f"No se puede iniciar evaluación "
            f"desde el estado '{self.nombre}'."
        )

    def aprobar(
        self,
        solicitud,
    ):
        raise TransicionInvalidaError(
            f"No se puede aprobar una solicitud "
            f"en estado '{self.nombre}'."
        )

    def solicitar_segunda_aprobacion(
        self,
        solicitud,
    ):
        raise TransicionInvalidaError(
            f"No se puede solicitar una segunda aprobación "
            f"desde el estado '{self.nombre}'."
        )

    def rechazar(
        self,
        solicitud,
        motivo="",
    ):
        raise TransicionInvalidaError(
            f"No se puede rechazar una solicitud "
            f"en estado '{self.nombre}'."
        )

    def _obtener_nombre_estado(
        self,
        estado,
    ):
        nombres = {
            "PENDIENTE": "Pendiente",
            "EN_EVALUACION": "En evaluación",
            "PENDIENTE_SEGUNDA_APROBACION": (
                "Pendiente de segunda aprobación"
            ),
            "APROBADA": "Aprobada",
            "RECHAZADA": "Rechazada",
        }

        return nombres.get(
            estado,
            estado,
        )

    def _crear_notificacion(
        self,
        solicitud,
        estado_anterior,
        nuevo_estado,
        comentario="",
    ):
        """
        Genera una notificación para el estudiante
        propietario de la solicitud.
        """

        from .models import Notificacion

        estado_anterior_texto = (
            self._obtener_nombre_estado(
                estado_anterior
            )
        )

        estado_nuevo_texto = (
            self._obtener_nombre_estado(
                nuevo_estado
            )
        )

        if nuevo_estado == "RECHAZADA":
            mensaje = (
                f"Tu solicitud #{solicitud.id} "
                f"ha sido rechazada."
            )

            if comentario:
                mensaje += (
                    f" Motivo: {comentario}"
                )

        elif nuevo_estado == "APROBADA":
            mensaje = (
                f"Tu solicitud #{solicitud.id} "
                f"ha sido aprobada."
            )

        elif (
            nuevo_estado
            == "PENDIENTE_SEGUNDA_APROBACION"
        ):
            mensaje = (
                f"Tu solicitud #{solicitud.id} "
                f"recibió la primera aprobación "
                f"y está pendiente de una segunda aprobación."
            )

        elif nuevo_estado == "EN_EVALUACION":
            mensaje = (
                f"Tu solicitud #{solicitud.id} "
                f"ha pasado a evaluación."
            )

        else:
            mensaje = (
                f"Tu solicitud #{solicitud.id} "
                f"cambió de "
                f"{estado_anterior_texto} a "
                f"{estado_nuevo_texto}."
            )

        Notificacion.objects.create(
            destinatario=solicitud.estudiante,
            solicitud=solicitud,
            mensaje=mensaje,
        )

    def _cambiar_estado(
        self,
        solicitud,
        nuevo_estado,
        comentario="",
    ):
        """
        Cambia el estado de la solicitud.

        También:
        - Registra el cambio en el historial.
        - Genera una notificación para el estudiante.
        """

        from .models import HistorialEstado

        estado_anterior = solicitud.estado

        solicitud.estado = nuevo_estado

        solicitud.save(
            update_fields=[
                "estado",
                "fecha_actualizacion",
            ]
        )

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

    def iniciar_evaluacion(
        self,
        solicitud,
    ):
        self._cambiar_estado(
            solicitud,
            "EN_EVALUACION",
        )


class EnEvaluacionState(EstadoSolicitud):
    nombre = "EN_EVALUACION"

    def aprobar(
        self,
        solicitud,
    ):
        """
        Aprobación directa para solicitudes
        que no requieren segunda aprobación.
        """

        self._cambiar_estado(
            solicitud,
            "APROBADA",
        )

    def solicitar_segunda_aprobacion(
        self,
        solicitud,
    ):
        """
        Primera aprobación de una solicitud
        mayor a Q10,000.
        """

        self._cambiar_estado(
            solicitud,
            "PENDIENTE_SEGUNDA_APROBACION",
            comentario=(
                "Solicitud pendiente de segunda aprobación."
            ),
        )

    def rechazar(
        self,
        solicitud,
        motivo="",
    ):
        solicitud.motivo_rechazo = motivo

        solicitud.save(
            update_fields=[
                "motivo_rechazo",
            ]
        )

        self._cambiar_estado(
            solicitud,
            "RECHAZADA",
            comentario=motivo,
        )


class PendienteSegundaAprobacionState(
    EstadoSolicitud
):
    """
    Estado utilizado cuando una solicitud
    mayor a Q10,000 ya recibió su primera aprobación.
    """

    nombre = "PENDIENTE_SEGUNDA_APROBACION"

    def aprobar(
        self,
        solicitud,
    ):
        """
        La segunda aprobación finaliza el proceso.
        """

        self._cambiar_estado(
            solicitud,
            "APROBADA",
            comentario=(
                "Segunda aprobación realizada."
            ),
        )

    def rechazar(
        self,
        solicitud,
        motivo="",
    ):
        """
        La segunda persona también puede rechazar
        la solicitud.
        """

        solicitud.motivo_rechazo = motivo

        solicitud.save(
            update_fields=[
                "motivo_rechazo",
            ]
        )

        self._cambiar_estado(
            solicitud,
            "RECHAZADA",
            comentario=motivo,
        )


class AprobadaState(EstadoSolicitud):
    """
    Estado final.
    """

    nombre = "APROBADA"


class RechazadaState(EstadoSolicitud):
    """
    Estado final.
    """

    nombre = "RECHAZADA"


_ESTADOS = {
    "PENDIENTE": PendienteState(),
    "EN_EVALUACION": EnEvaluacionState(),
    "PENDIENTE_SEGUNDA_APROBACION": (
        PendienteSegundaAprobacionState()
    ),
    "APROBADA": AprobadaState(),
    "RECHAZADA": RechazadaState(),
}


def obtener_estado(
    nombre_estado: str,
) -> EstadoSolicitud:
    """
    Devuelve el objeto correspondiente
    al estado actual de la solicitud.
    """

    try:
        return _ESTADOS[
            nombre_estado
        ]

    except KeyError:
        raise ValueError(
            f"Estado desconocido: {nombre_estado}"
        )