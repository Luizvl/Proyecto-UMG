"""
Patrón de diseño: FACADE (estructural)

SolicitudService centraliza la lógica de negocio relacionada
con las solicitudes de beca.
"""

from django.core.exceptions import ValidationError

from apps.convocatorias.models import Convocatoria

from .models import Documento, Solicitud


class SolicitudService:
    """
    Fachada del subsistema de solicitudes.
    """

    @staticmethod
    def crear_solicitud(
        estudiante,
        convocatoria: Convocatoria,
    ) -> Solicitud:
        """
        Crea una solicitud validando las reglas de negocio.
        """

        if not convocatoria.esta_abierta():
            raise ValidationError(
                "La convocatoria no está activa o se encuentra fuera de fecha."
            )

        if Solicitud.objects.filter(
            estudiante=estudiante,
            convocatoria=convocatoria,
        ).exists():
            raise ValidationError(
                "El estudiante ya tiene una solicitud para esta convocatoria."
            )

        return Solicitud.objects.create(
            estudiante=estudiante,
            convocatoria=convocatoria,
        )

    @staticmethod
    def agregar_documento(
        solicitud: Solicitud,
        archivo,
        tipo: str,
    ) -> Documento:
        """
        Agrega un documento a una solicitud.
        """

        return Documento.objects.create(
            solicitud=solicitud,
            archivo=archivo,
            tipo=tipo,
        )

    @staticmethod
    def iniciar_evaluacion(
        solicitud: Solicitud,
    ) -> None:
        """
        Cambia la solicitud de PENDIENTE
        a EN_EVALUACION.
        """

        solicitud.iniciar_evaluacion()

    @staticmethod
    def aprobar(
        solicitud: Solicitud,
    ) -> None:
        """
        Aprueba una solicitud siempre que la convocatoria
        todavía tenga cupo disponible.
        """

        convocatoria = solicitud.convocatoria

        aprobadas = Solicitud.objects.filter(
            convocatoria=convocatoria,
            estado=Solicitud.APROBADA,
        ).exclude(
            pk=solicitud.pk,
        ).count()

        if aprobadas >= convocatoria.cupo:
            raise ValidationError(
                "La convocatoria ya alcanzó el cupo máximo "
                "de becas aprobadas."
            )

        solicitud.aprobar()

    @staticmethod
    def rechazar(
        solicitud: Solicitud,
        motivo: str = "",
    ) -> None:
        """
        Rechaza una solicitud indicando el motivo.
        """

        if not motivo.strip():
            raise ValidationError(
                "Debe indicar el motivo del rechazo."
            )

        solicitud.rechazar(motivo)