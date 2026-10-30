from decimal import Decimal, InvalidOperation
 
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
 
from apps.convocatorias.models import Convocatoria
 
from .models import AuditoriaSolicitud, Documento, Solicitud
 
 
class SolicitudService:
    """
    Fachada del subsistema de solicitudes.
    """
 
    LIMITE_SEGUNDA_APROBACION = Decimal("10000.00")
 
    @staticmethod
    def _registrar_auditoria(
        solicitud: Solicitud,
        usuario,
        accion: str,
        resultado: str,
    ) -> AuditoriaSolicitud:
        """
        Crea el registro de auditoría de una acción.
 
        Se invoca siempre desde métodos con @transaction.atomic,
        de modo que si la auditoría falla, la acción se revierte.
        """
 
        return AuditoriaSolicitud.objects.create(
            solicitud=solicitud,
            usuario=usuario,
            accion=accion,
            resultado=resultado,
        )
 
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
            monto_solicitado = Decimal(str(monto_solicitado))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError(
                "El monto solicitado no es válido."
            )
 
        if not monto_solicitado.is_finite():
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
    @transaction.atomic
    def iniciar_evaluacion(
        solicitud: Solicitud,
        usuario=None,
    ) -> None:
        """
        Cambia la solicitud de PENDIENTE
        a EN_EVALUACION y registra la auditoría.
        """
 
        solicitud.iniciar_evaluacion()
 
        SolicitudService._registrar_auditoria(
            solicitud,
            usuario,
            "Iniciar Evaluación",
            "El estado de la solicitud cambió a En Evaluación.",
        )
 
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
    @transaction.atomic
    def aprobar(
        solicitud: Solicitud,
        aprobador,
    ) -> None:
        """
        Procesa la aprobación de una solicitud y registra
        la auditoría correspondiente a cada paso.
 
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
 
        # --- Aprobación única (monto <= límite) ---
        if monto <= SolicitudService.LIMITE_SEGUNDA_APROBACION:
            if solicitud.estado != Solicitud.EN_EVALUACION:
                raise ValidationError(
                    "La solicitud no se encuentra en un estado válido "
                    "para ser aprobada (estado actual: "
                    f"{solicitud.get_estado_display()}). "
                    "Debe estar En Evaluación."
                )
 
            SolicitudService._validar_cupo(solicitud)
 
            solicitud.primer_aprobador = aprobador
            solicitud.fecha_primera_aprobacion = timezone.now()
 
            solicitud.save(
                update_fields=[
                    "primer_aprobador",
                    "fecha_primera_aprobacion",
                ]
            )
 
            solicitud.aprobar()
 
            SolicitudService._registrar_auditoria(
                solicitud,
                aprobador,
                "Aprobación de Solicitud",
                "Solicitud aprobada (aprobación única).",
            )
 
            return
 
        # --- Primera aprobación (monto > límite) ---
        if solicitud.estado == Solicitud.EN_EVALUACION:
            solicitud.primer_aprobador = aprobador
            solicitud.fecha_primera_aprobacion = timezone.now()
 
            solicitud.save(
                update_fields=[
                    "primer_aprobador",
                    "fecha_primera_aprobacion",
                ]
            )
 
            solicitud.solicitar_segunda_aprobacion()
 
            SolicitudService._registrar_auditoria(
                solicitud,
                aprobador,
                "Primera aprobación",
                "Pendiente de segunda aprobación "
                "(monto superior a Q10,000).",
            )
 
            return
 
        # --- Segunda aprobación (monto > límite) ---
        if solicitud.estado == Solicitud.PENDIENTE_SEGUNDA_APROBACION:
            if solicitud.primer_aprobador_id == aprobador.id:
                raise ValidationError(
                    "La segunda aprobación debe ser "
                    "realizada por una persona distinta "
                    "a quien realizó la primera aprobación."
                )
 
            SolicitudService._validar_cupo(solicitud)
 
            solicitud.segundo_aprobador = aprobador
            solicitud.fecha_segunda_aprobacion = timezone.now()
 
            solicitud.save(
                update_fields=[
                    "segundo_aprobador",
                    "fecha_segunda_aprobacion",
                ]
            )
 
            solicitud.aprobar()
 
            SolicitudService._registrar_auditoria(
                solicitud,
                aprobador,
                "Segunda aprobación",
                "Solicitud aprobada definitivamente.",
            )
 
            return
 
        raise ValidationError(
            "La solicitud no se encuentra en un estado válido "
            "para ser aprobada (estado actual: "
            f"{solicitud.get_estado_display()})."
        )
 
    @staticmethod
    @transaction.atomic
    def rechazar(
        solicitud: Solicitud,
        motivo: str = "",
        usuario=None,
    ) -> None:
        """
        Rechaza una solicitud indicando el motivo y
        registra la auditoría del rechazo.
        """
 
        motivo = motivo.strip()
 
        if not motivo:
            raise ValidationError(
                "Debe indicar el motivo del rechazo."
            )
 
        solicitud.rechazar(motivo)
 
        SolicitudService._registrar_auditoria(
            solicitud,
            usuario,
            "Rechazo de Solicitud",
            f"Se rechazó la solicitud. Motivo: {motivo}",
        )
 