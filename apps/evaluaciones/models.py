from django.conf import settings
from django.db import models

from apps.solicitudes.models import Solicitud


class Comite(models.Model):
    """Comité evaluador. Un comité agrupa varios usuarios evaluadores."""
    nombre = models.CharField(max_length=100)
    convocatoria = models.ForeignKey(
        "convocatorias.Convocatoria", on_delete=models.CASCADE, related_name="comites"
    )
    integrantes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="comites")

    class Meta:
        verbose_name = "Comité Evaluador"
        verbose_name_plural = "Comités Evaluadores"

    def __str__(self):
        return self.nombre


class Evaluacion(models.Model):
    """Evaluación individual que un miembro de comité hace sobre una solicitud."""
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name="evaluaciones")
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        unique_together = ("solicitud", "evaluador")

    def __str__(self):
        return f"Eval. {self.evaluador} -> Solicitud #{self.solicitud_id}: {self.puntaje}"
