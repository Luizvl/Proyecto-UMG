from django.contrib import admin
from .models import Convocatoria


@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_beca", "estado", "fecha_inicio", "fecha_fin", "cupo")
    list_filter = ("estado", "tipo_beca")
    search_fields = ("nombre",)
