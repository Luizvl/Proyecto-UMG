from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    class Rol(models.TextChoices):
        ESTUDIANTE = "ESTUDIANTE", "Estudiante"
        COMITE = "COMITE", "Miembro del Comité"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico"
    )

    dpi = models.CharField(
        max_length=13,
        unique=True,
        null=True,
        blank=True,
        verbose_name="DPI"
    )

    telefono = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Teléfono"
    )

    direccion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Dirección"
    )

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.ESTUDIANTE
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} - {self.get_rol_display()}"