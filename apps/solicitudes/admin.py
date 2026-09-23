from django.contrib import admin
from .models import Documento, HistorialEstado, Solicitud


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = ("estado_anterior", "estado_nuevo", "fecha", "comentario")
    can_delete = False


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ("id", "estudiante", "convocatoria", "estado", "fecha_creacion")
    list_filter = ("estado", "convocatoria")
    search_fields = ("estudiante__dpi", "estudiante__email")
    inlines = [DocumentoInline, HistorialEstadoInline]
