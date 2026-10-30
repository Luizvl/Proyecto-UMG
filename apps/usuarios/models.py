from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """
    Manager personalizado para asegurar que los superusuarios creados por consola
    nazcan automáticamente con el rol ADMINISTRADOR.
    """
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "ADMINISTRADOR")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


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

    # Conectamos el manager personalizado
    objects = CustomUserManager()

    def __str__(self):
        # Corregido: el salto de línea rompía la sintaxis de Python. 
        # Ahora se mostrará limpio, ej: "alvaro@admin.com (Administrador)"
        return f"{self.email} ({self.get_rol_display()})"

    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE

    def save(self, *args, **kwargs):
        # Candado de seguridad: Sincroniza el rol ADMINISTRADOR con los permisos de Django.
        # Esto soluciona tu problema de los menús desplegables en el panel /admin, 
        # garantizando que tengas acceso total (ver, agregar, cambiar, eliminar).
        if self.is_superuser or self.is_staff:
            self.rol = self.Rol.ADMINISTRADOR
            self.is_staff = True
            self.is_superuser = True
            
        super().save(*args, **kwargs)