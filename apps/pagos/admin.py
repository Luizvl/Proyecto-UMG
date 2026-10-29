from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from apps.solicitudes.models import Solicitud

from .models import CondicionPago, Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("id", "estudiante", "solicitud", "concepto", "monto_pagado",
                    "estado", "miniatura", "fecha_creacion")
    list_filter = ("estado",)
    search_fields = ("estudiante__email", "estudiante__dpi", "concepto")
    readonly_fields = ("miniatura", "fecha_creacion", "fecha_actualizacion")
    actions = ["aprobar_pagos", "rechazar_pagos"]

    @admin.display(description="Comprobante")
    def miniatura(self, obj):
        if obj.comprobante:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="height:60px;border-radius:6px;"></a>',
                obj.comprobante.url, obj.comprobante.url,
            )
        return "—"

    @admin.action(description="Aprobar pagos seleccionados")
    def aprobar_pagos(self, request, queryset):
        n = queryset.filter(estado=Pago.PENDIENTE).update(
            estado=Pago.APROBADO, fecha_actualizacion=timezone.now())
        self.message_user(request, f"{n} pago(s) aprobado(s).")

    @admin.action(description="Rechazar pagos seleccionados")
    def rechazar_pagos(self, request, queryset):
        n = queryset.filter(estado=Pago.PENDIENTE).update(
            estado=Pago.RECHAZADO, fecha_actualizacion=timezone.now())
        self.message_user(request, f"{n} pago(s) rechazado(s). Escribe el motivo en 'Notas admin' de cada uno.")


@admin.register(CondicionPago)
class CondicionPagoAdmin(admin.ModelAdmin):
    list_display = ("solicitud", "cobertura_porcentaje", "monto_base", "monto_calculado")

    @admin.display(description="Paga el estudiante")
    def monto_calculado(self, obj):
        return f"Q{obj.monto_a_pagar}"

    def get_readonly_fields(self, request, obj=None):
        return ("solicitud",) if obj else ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Solo muestra solicitudes aprobadas que todavía no tienen condición
        if db_field.name == "solicitud":
            kwargs["queryset"] = Solicitud.objects.filter(
                estado=Solicitud.APROBADA, condicion_pago__isnull=True
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)