from django.db import models


class Convocatoria(models.Model):
    """Entidad de dominio: Convocatoria de beca."""

    ESTADO_ACTIVA = "ACTIVA"
    ESTADO_CERRADA = "CERRADA"
    ESTADOS = [
        (ESTADO_ACTIVA, "Activa"),
        (ESTADO_CERRADA, "Cerrada"),
    ]

    nombre = models.CharField(max_length=150)
    tipo_beca = models.CharField(
        max_length=20,
        choices=[
            ("MEDIO", "Nivel Medio"),
            ("UNIVERSITARIO", "Universitario"),
            ("POSGRADO", "Posgrado"),
        ],
    )
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cupo = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default=ESTADO_ACTIVA)

    class Meta:
        verbose_name = "Convocatoria"
        verbose_name_plural = "Convocatorias"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

    def esta_abierta(self):
        return self.estado == self.ESTADO_ACTIVA
