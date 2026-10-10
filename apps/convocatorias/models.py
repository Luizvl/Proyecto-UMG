from django.db import models
from django.utils import timezone


class Convocatoria(models.Model):
    """
    Entidad de dominio: Convocatoria de beca.
    """

    ESTADO_ACTIVA = "ACTIVA"
    ESTADO_CERRADA = "CERRADA"

    ESTADOS = [
        (ESTADO_ACTIVA, "Activa"),
        (ESTADO_CERRADA, "Cerrada"),
    ]

    TIPO_MEDIO = "MEDIO"
    TIPO_UNIVERSITARIO = "UNIVERSITARIO"
    TIPO_POSGRADO = "POSGRADO"

    TIPOS_BECA = [
        (TIPO_MEDIO, "Nivel Medio"),
        (TIPO_UNIVERSITARIO, "Universitario"),
        (TIPO_POSGRADO, "Posgrado"),
    ]

    nombre = models.CharField(
        max_length=150
    )

    tipo_beca = models.CharField(
        max_length=20,
        choices=TIPOS_BECA,
    )

    descripcion = models.TextField(
        blank=True
    )

    fecha_inicio = models.DateField()

    fecha_fin = models.DateField()

    cupo = models.PositiveIntegerField(
        default=1
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default=ESTADO_ACTIVA,
    )

    class Meta:
        verbose_name = "Convocatoria"
        verbose_name_plural = "Convocatorias"
        ordering = [
            "-fecha_inicio"
        ]

    def __str__(self):
        return (
            f"{self.nombre} "
            f"({self.get_estado_display()})"
        )

    def esta_abierta(self):
        """
        La convocatoria está abierta únicamente si:

        - Su estado es ACTIVA.
        - Ya inició.
        - Todavía no venció.
        """

        hoy = timezone.localdate()

        return (
            self.estado == self.ESTADO_ACTIVA
            and self.fecha_inicio <= hoy
            and hoy <= self.fecha_fin
        )