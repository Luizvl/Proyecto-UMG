from django.contrib import admin
from django.utils.html import format_html
from .models import Documento, HistorialEstado, Solicitud

# ==============================================================================
# INLINES (De Byron)
# ==============================================================================
class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0

class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = ("estado_anterior", "estado_nuevo", "fecha", "comentario")
    can_delete = False


# ==============================================================================
# ADMIN PRINCIPAL (Diseño y Acciones fusionadas)
# ==============================================================================
@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    # 1. Cambiamos 'estado' por 'estado_badge'
    list_display = ("id", "estudiante", "convocatoria", "estado_badge", "fecha_creacion")
    list_filter = ("estado", "convocatoria")
    search_fields = ("estudiante__dpi", "estudiante__email")
    inlines = [DocumentoInline, HistorialEstadoInline]
    
    # 2. Registramos las acciones masivas
    actions = ['marcar_en_evaluacion', 'aprobar_solicitudes', 'rechazar_solicitudes']

    # --------------------------------------------------------------------------
    # DISEÑO: Etiquetas de Colores
    # --------------------------------------------------------------------------
    @admin.display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        colores = {
            'PENDIENTE': 'warning',         # Amarillo
            'EN_EVALUACION': 'primary',     # Azul
            'APROBADA': 'success',          # Verde
            'RECHAZADA': 'danger',          # Rojo
        }
        color = colores.get(obj.estado, 'secondary')
        
        return format_html(
            '<span class="badge badge-{}" style="font-size: 0.9em; padding: 6px 10px;">{}</span>',
            color,
            obj.get_estado_display()
        )

    # --------------------------------------------------------------------------
    # ACCIONES MASIVAS (Conectadas al Patrón State del backend)
    # --------------------------------------------------------------------------
    @admin.action(description='Marcar seleccionadas como "En Evaluación"')
    def marcar_en_evaluacion(self, request, queryset):
        exito = 0
        for solicitud in queryset:
            try:
                solicitud.iniciar_evaluacion()  # Dispara la función de Byron
                exito += 1
            except Exception:
                pass # Ignora si la transición de estado no es permitida
        self.message_user(request, f'{exito} solicitudes pasaron a evaluación.')

    @admin.action(description='Aprobar solicitudes seleccionadas')
    def aprobar_solicitudes(self, request, queryset):
        exito = 0
        for solicitud in queryset:
            try:
                solicitud.aprobar() # Dispara la función de Byron
                exito += 1
            except Exception:
                pass
        self.message_user(request, f'{exito} solicitudes aprobadas exitosamente.', level='success')

    @admin.action(description='Rechazar solicitudes seleccionadas')
    def rechazar_solicitudes(self, request, queryset):
        exito = 0
        for solicitud in queryset:
            try:
                solicitud.rechazar(motivo="Rechazo masivo desde el panel de administración.")
                exito += 1
            except Exception:
                pass
        self.message_user(request, f'{exito} solicitudes han sido rechazadas.', level='warning')