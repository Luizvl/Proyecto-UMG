from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.convocatorias.models import Convocatoria

from .models import Documento, Solicitud


class SolicitudService:
    """
    Fachada del subsistema de solicitudes.
    """

    LIMITE_SEGUNDA_APROBACION = Decimal("10000.00")

    @staticmethod
    def crear_solicitud(
        estudiante,
        convocatoria: Convocatoria,
        motivo: str = "",
        monto_solicitado=0,
    ) -> Solicitud:
        """
        Crea una solicitud validando las reglas de negocio.
        """

        if not convocatoria.esta_abierta():
            raise ValidationError(
                "La convocatoria no está activa "
                "o se encuentra fuera de fecha."
            )

        if Solicitud.objects.filter(
            estudiante=estudiante,
            convocatoria=convocatoria,
        ).exists():
            raise ValidationError(
                "El estudiante ya tiene una solicitud "
                "para esta convocatoria."
            )

        motivo = motivo.strip()

        if len(motivo) > 1000:
            raise ValidationError(
                "El motivo no puede superar los "
                "1000 caracteres."
            )

        try:
            monto_solicitado = Decimal(
                str(monto_solicitado)
            )
        except Exception:
            raise ValidationError(
                "El monto solicitado no es válido."
            )

        if monto_solicitado < 0:
            raise ValidationError(
                "El monto solicitado no puede ser negativo."
            )

        return Solicitud.objects.create(
            estudiante=estudiante,
            convocatoria=convocatoria,
            motivo=motivo,
            monto_solicitado=monto_solicitado,
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
    def _validar_cupo(
        solicitud: Solicitud,
    ) -> None:
        """
        Verifica que la convocatoria todavía
        tenga cupo disponible.
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
                "La convocatoria ya alcanzó el "
                "cupo máximo de becas aprobadas."
            )

    @staticmethod
    def aprobar(
        solicitud: Solicitud,
        aprobador,
    ) -> None:
        """
        Procesa la aprobación de una solicitud.

        Hasta Q10,000:
        - Una sola aprobación.

        Mayor a Q10,000:
        - Primera aprobación:
          EN_EVALUACION ->
          PENDIENTE_SEGUNDA_APROBACION

        - Segunda aprobación:
          PENDIENTE_SEGUNDA_APROBACION ->
          APROBADA

        La segunda aprobación debe ser realizada
        por una persona distinta.
        """

        monto = solicitud.monto_solicitado

        if monto <= SolicitudService.LIMITE_SEGUNDA_APROBACION:
            SolicitudService._validar_cupo(
                solicitud
            )

            solicitud.primer_aprobador = aprobador
            solicitud.fecha_primera_aprobacion = (
                timezone.now()
            )

            solicitud.save(
                update_fields=[
                    "primer_aprobador",
                    "fecha_primera_aprobacion",
                ]
            )

            solicitud.aprobar()

            return

        if (
            solicitud.estado
            == Solicitud.EN_EVALUACION
        ):
            solicitud.primer_aprobador = aprobador
            solicitud.fecha_primera_aprobacion = (
                timezone.now()
            )

            solicitud.save(
                update_fields=[
                    "primer_aprobador",
                    "fecha_primera_aprobacion",
                ]
            )

            solicitud.solicitar_segunda_aprobacion()

            return

        if (
            solicitud.estado
            == Solicitud.PENDIENTE_SEGUNDA_APROBACION
        ):
            if (
                solicitud.primer_aprobador_id
                == aprobador.id
            ):
                raise ValidationError(
                    "La segunda aprobación debe ser "
                    "realizada por una persona distinta "
                    "a quien realizó la primera aprobación."
                )

            SolicitudService._validar_cupo(
                solicitud
            )

            solicitud.segundo_aprobador = aprobador
            solicitud.fecha_segunda_aprobacion = (
                timezone.now()
            )

            solicitud.save(
                update_fields=[
                    "segundo_aprobador",
                    "fecha_segunda_aprobacion",
                ]
            )

            solicitud.aprobar()

            return

        raise ValidationError(
            "La solicitud no se encuentra en un "
            "estado válido para ser aprobada."
        )

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

        solicitud.rechazar(
            motivo
        )