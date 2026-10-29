from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.usuarios.models import Usuario


class Pago(models.Model):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"

    ESTADOS_PAGO = (
        (PENDIENTE, "Pendiente de Revisión"),
        (APROBADO, "Aprobado"),
        (RECHAZADO, "Rechazado"),
    )

    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="pagos")
    solicitud = models.ForeignKey(
        "solicitudes.Solicitud",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos",
    )
    concepto = models.CharField(max_length=200, help_text="Ej: Colegiatura Octubre - Media Beca")
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cantidad pagada en Quetzales")
    comprobante = models.ImageField(upload_to="comprobantes_pago/%Y/%m/", help_text="Foto o captura del recibo de pago")
    estado = models.CharField(max_length=20, choices=ESTADOS_PAGO, default=PENDIENTE)
    notas_admin = models.TextField(
        blank=True,
        null=True,
        help_text="Razón de rechazo o nota interna (visible para el estudiante)",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Pago #{self.pk} - Q{self.monto_pagado}"


class CondicionPago(models.Model):
    """Cobertura de la beca y monto de inscripción de una solicitud aprobada."""

    solicitud = models.OneToOneField(
        "solicitudes.Solicitud",
        on_delete=models.CASCADE,
        related_name="condicion_pago",
    )
    cobertura_porcentaje = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="100 = beca completa, 50 = media beca",
    )
    monto_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Monto de inscripción en Quetzales, antes de aplicar la beca",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Condición de pago"
        verbose_name_plural = "Condiciones de pago"

    def __str__(self):
        return f"Solicitud #{self.solicitud_id}: {self.cobertura_porcentaje}% de cobertura"

    @property
    def monto_a_pagar(self):
        factor = Decimal(100 - self.cobertura_porcentaje) / Decimal(100)
        return (self.monto_base * factor).quantize(Decimal("0.01"))

    @property
    def descripcion_cobertura(self):
        if self.cobertura_porcentaje == 100:
            return "Beca completa"
        if self.cobertura_porcentaje == 50:
            return "Media beca"
        return f"Beca del {self.cobertura_porcentaje}%"