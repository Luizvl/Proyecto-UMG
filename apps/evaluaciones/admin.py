from django.contrib import admin
from .models import Comite, Evaluacion


@admin.register(Comite)
class ComiteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "convocatoria")
    filter_horizontal = ("integrantes",)


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ("solicitud", "evaluador", "puntaje", "fecha")
    list_filter = ("evaluador",)
