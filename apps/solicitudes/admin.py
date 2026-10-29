from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Documento,
    HistorialEstado,
    Solicitud,
    AuditoriaSolicitud,
)


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


# ==========================================================
# ADMINISTRACIÓN DE SOLICITUDES
# ==========================================================

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "estudiante",
        "convocatoria",
        "estado_badge",
        "fecha_creacion",
    )

    list_filter = ("estado", "convocatoria")

    search_fields = (
        "estudiante__dpi",
        "estudiante__email",
    )

    inlines = [
        DocumentoInline,
        HistorialEstadoInline,
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
    # ACCIÓN MASIVA: INICIAR EVALUACIÓN
    # ------------------------------------------------------

    @admin.action(
        description='Marcar seleccionadas como "En Evaluación"'
    )
    def marcar_en_evaluacion(self, request, queryset):
        exito = 0

        for solicitud in queryset:
            try:
                solicitud.iniciar_evaluacion()
                exito += 1
            except Exception:
                continue

        self.message_user(
            request,
            f"{exito} solicitudes pasaron a evaluación.",
        )

    # ------------------------------------------------------
    # ACCIÓN MASIVA: APROBAR
    # ------------------------------------------------------

    @admin.action(
        description="Aprobar solicitudes seleccionadas"
    )
    def aprobar_solicitudes(self, request, queryset):
        exito = 0

        for solicitud in queryset:
            try:
                solicitud.aprobar()
                exito += 1
            except Exception:
                continue

        self.message_user(
            request,
            f"{exito} solicitudes aprobadas exitosamente.",
            level="success",
        )

    # ------------------------------------------------------
    # ACCIÓN MASIVA: RECHAZAR
    # ------------------------------------------------------

    @admin.action(
        description="Rechazar solicitudes seleccionadas"
    )
    def rechazar_solicitudes(self, request, queryset):
        exito = 0

        for solicitud in queryset:
            try:
                solicitud.rechazar(
                    motivo=(
                        "Rechazo masivo desde el panel "
                        "de administración."
                    )
                )
                exito += 1
            except Exception:
                continue

        self.message_user(
            request,
            f"{exito} solicitudes han sido rechazadas.",
            level="warning",
        )


# ==========================================================
# ADMINISTRACIÓN DE LA BITÁCORA DE AUDITORÍA (Tu módulo intacto)
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

    search_fields = (
        "solicitud__id",
        "usuario__username",
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