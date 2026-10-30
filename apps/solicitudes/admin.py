from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import (
    AuditoriaSolicitud,
    Documento,
    HistorialEstado,
    Solicitud,
)
from .services import SolicitudService


# ==========================================================
# INLINES
# ==========================================================

class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = (
        "estado_anterior",
        "estado_nuevo",
        "fecha",
        "comentario",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class AuditoriaSolicitudInline(admin.TabularInline):
    """Muestra (solo lectura) la bitácora de auditoría de la solicitud."""
    model = AuditoriaSolicitud
    extra = 0
    fields = ("fecha", "usuario", "accion", "resultado")
    readonly_fields = ("fecha", "usuario", "accion", "resultado")
    can_delete = False
    verbose_name = "Registro de auditoría"
    verbose_name_plural = "Registros de auditoría"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ==========================================================
# ADMINISTRACIÓN DE SOLICITUDES
# ==========================================================

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "estudiante",
        "convocatoria",
        "monto_solicitado",
        "estado_badge",
        "fecha_creacion",
    )

    list_filter = ("estado", "convocatoria")

    list_select_related = ("estudiante", "convocatoria")

    search_fields = (
        "estudiante__dpi",
        "estudiante__email",
    )

    # Los datos de aprobación los asigna el servicio, no se editan a mano.
    # El campo "estado" SÍ se puede cambiar en el formulario, pero el
    # cambio se procesa en save_model() a través de SolicitudService
    # (así respeta reglas, historial, cupo, doble aprobación y auditoría).
    readonly_fields = (
        "primer_aprobador",
        "fecha_primera_aprobacion",
        "segundo_aprobador",
        "fecha_segunda_aprobacion",
        "fecha_creacion",
        "fecha_actualizacion",
    )

    inlines = [
        DocumentoInline,
        HistorialEstadoInline,
        AuditoriaSolicitudInline,
    ]

    actions = [
        "marcar_en_evaluacion",
        "aprobar_solicitudes",
        "rechazar_solicitudes",
    ]

    # ------------------------------------------------------
    # ETIQUETAS DE COLORES PARA LOS ESTADOS
    # ------------------------------------------------------

    @admin.display(description="Estado", ordering="estado")
    def estado_badge(self, obj):
        colores = {
            "PENDIENTE": "warning",
            "EN_EVALUACION": "primary",
            "PENDIENTE_SEGUNDA_APROBACION": "info",
            "APROBADA": "success",
            "RECHAZADA": "danger",
        }

        color = colores.get(obj.estado, "secondary")

        return format_html(
            '<span class="badge badge-{}" '
            'style="font-size: 0.9em; padding: 6px 10px;">'
            '{}'
            '</span>',
            color,
            obj.get_estado_display(),
        )

    # ------------------------------------------------------
    # CAMPOS VISIBLES SEGÚN EL MONTO
    # ------------------------------------------------------

    def get_fields(self, request, obj=None):
        """
        El segundo aprobador solo aplica cuando el monto supera el
        límite (Q10,000); en los demás casos se oculta. Al crear una
        solicitud nueva no se muestran los datos de aprobación.
        """
        campos = list(super().get_fields(request, obj))

        ocultar = []
        if obj is None:
            ocultar = [
                "primer_aprobador",
                "fecha_primera_aprobacion",
                "segundo_aprobador",
                "fecha_segunda_aprobacion",
            ]
        elif obj.monto_solicitado <= SolicitudService.LIMITE_SEGUNDA_APROBACION:
            ocultar = ["segundo_aprobador", "fecha_segunda_aprobacion"]

        return [campo for campo in campos if campo not in ocultar]

    # ------------------------------------------------------
    # CAMBIO DE ESTADO DESDE EL FORMULARIO DE DETALLE
    # ------------------------------------------------------

    def save_model(self, request, obj, form, change):
        """
        Si se cambió el campo "estado" en el formulario, la transición
        se ejecuta mediante SolicitudService en lugar de guardar el
        valor directamente.
        """
        if not (change and "estado" in form.changed_data):
            super().save_model(request, obj, form, change)
            return

        nuevo_estado = obj.estado
        # Se guardan los demás campos con el estado original; la
        # transición la aplica el servicio.
        obj.estado = form.initial.get("estado", obj.estado)
        super().save_model(request, obj, form, change)

        try:
            self._aplicar_transicion(request, obj, nuevo_estado)
        except ValidationError as exc:
            self.message_user(
                request,
                f"No se pudo cambiar el estado: {' '.join(exc.messages)}",
                messages.ERROR,
            )

    def _aplicar_transicion(self, request, obj, nuevo_estado):
        if nuevo_estado == Solicitud.EN_EVALUACION:
            SolicitudService.iniciar_evaluacion(obj, request.user)

        elif nuevo_estado == Solicitud.APROBADA:
            SolicitudService.aprobar(obj, request.user)

            if obj.estado == Solicitud.PENDIENTE_SEGUNDA_APROBACION:
                self.message_user(
                    request,
                    "El monto supera Q10,000: quedó pendiente de una "
                    "segunda aprobación por otra persona.",
                    messages.INFO,
                )

        elif nuevo_estado == Solicitud.RECHAZADA:
            # Se usa el texto del campo "Motivo rechazo" del formulario.
            SolicitudService.rechazar(
                obj,
                obj.motivo_rechazo,
                request.user,
            )

        else:
            raise ValidationError(
                "Ese estado no se puede asignar manualmente; "
                "se asigna automáticamente según el flujo."
            )

    # ------------------------------------------------------
    # UTILIDAD: EJECUTAR UNA ACCIÓN MASIVA CON REPORTE REAL
    # ------------------------------------------------------

    def _ejecutar_masivo(self, request, queryset, funcion, mensaje_exito):
        """
        Aplica `funcion` a cada solicitud usando el servicio.
        Informa cuántas salieron bien y el motivo de cada error,
        en lugar de ocultar los fallos.
        """
        exitos = 0
        errores = []

        for solicitud in queryset:
            try:
                funcion(solicitud)
                exitos += 1
            except ValidationError as exc:
                errores.append(
                    f"Solicitud #{solicitud.pk}: {' '.join(exc.messages)}"
                )

        if exitos:
            self.message_user(
                request,
                mensaje_exito.format(n=exitos),
                messages.SUCCESS,
            )

        limite = 10
        for error in errores[:limite]:
            self.message_user(request, error, messages.ERROR)

        if len(errores) > limite:
            self.message_user(
                request,
                f"... y {len(errores) - limite} errores más.",
                messages.ERROR,
            )

        if not exitos and not errores:
            self.message_user(
                request,
                "No se seleccionó ninguna solicitud.",
                messages.WARNING,
            )

    # ------------------------------------------------------
    # ACCIÓN MASIVA: INICIAR EVALUACIÓN
    # ------------------------------------------------------

    @admin.action(
        description='Marcar seleccionadas como "En Evaluación"'
    )
    def marcar_en_evaluacion(self, request, queryset):
        self._ejecutar_masivo(
            request,
            queryset,
            lambda s: SolicitudService.iniciar_evaluacion(s, request.user),
            "{n} solicitudes pasaron a evaluación.",
        )

    # ------------------------------------------------------
    # ACCIÓN MASIVA: APROBAR
    # ------------------------------------------------------

    @admin.action(
        description="Aprobar solicitudes seleccionadas"
    )
    def aprobar_solicitudes(self, request, queryset):
        # Respeta cupo y doble aprobación (> Q10,000) y deja auditoría.
        self._ejecutar_masivo(
            request,
            queryset,
            lambda s: SolicitudService.aprobar(s, request.user),
            "{n} solicitudes procesadas (aprobadas o enviadas "
            "a segunda aprobación).",
        )

    # ------------------------------------------------------
    # ACCIÓN MASIVA: RECHAZAR
    # ------------------------------------------------------

    @admin.action(
        description="Rechazar solicitudes seleccionadas"
    )
    def rechazar_solicitudes(self, request, queryset):
        self._ejecutar_masivo(
            request,
            queryset,
            lambda s: SolicitudService.rechazar(
                s,
                "Rechazo masivo desde el panel de administración.",
                request.user,
            ),
            "{n} solicitudes han sido rechazadas.",
        )


# ==========================================================
# ADMINISTRACIÓN DE LA BITÁCORA DE AUDITORÍA
# ==========================================================

@admin.register(AuditoriaSolicitud)
class AuditoriaSolicitudAdmin(admin.ModelAdmin):

    list_display = (
        "fecha",
        "solicitud",
        "usuario",
        "accion",
    )

    list_filter = (
        "accion",
        "fecha",
        "usuario",
    )

    list_select_related = ("solicitud", "usuario")

    # "=" => coincidencia exacta del id; email en lugar de username
    # porque SolicitudAdmin ya busca por email (el modelo de usuario
    # no necesariamente tiene username).
    search_fields = (
        "=solicitud__id",
        "usuario__email",
        "resultado",
    )

    readonly_fields = (
        "solicitud",
        "usuario",
        "accion",
        "resultado",
        "fecha",
    )

    ordering = ("-fecha",)

    # Impide crear registros manualmente desde el panel.
    def has_add_permission(self, request):
        return False

    # Impide modificar registros de auditoría.
    def has_change_permission(self, request, obj=None):
        return False

    # Impide eliminar registros desde el panel.
    def has_delete_permission(self, request, obj=None):
        return False