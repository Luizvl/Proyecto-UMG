from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario del sistema, con rol integrado (Estudiante / Comité / Administrador).

    Reemplaza al User estándar de Django (AUTH_USER_MODEL en settings.py)
    para poder guardar DPI, teléfono, dirección y rol directamente sobre
    el usuario, evitando un modelo Estudiante separado y duplicado.
    """

    class Rol(models.TextChoices):
        ESTUDIANTE = "ESTUDIANTE", "Estudiante"
        COMITE = "COMITE", "Miembro del Comité"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    class NivelAcademico(models.TextChoices):
        MEDIO = "MEDIO", "Nivel Medio"
        UNIVERSITARIO = "UNIVERSITARIO", "Universitario"
        POSGRADO = "POSGRADO", "Posgrado"

    email = models.EmailField(unique=True, verbose_name="Correo electrónico")

    dpi = models.CharField(
        max_length=13, unique=True, null=True, blank=True, verbose_name="DPI"
    )
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ESTUDIANTE)

    # Solo aplica cuando rol = ESTUDIANTE; se deja opcional para comité/administrador.
    nivel_academico = models.CharField(
        max_length=20, choices=NivelAcademico.choices, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} - {self.get_rol_display()}"

    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE
