from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("email", "username", "rol", "dpi", "is_staff")
    list_filter = ("rol", "nivel_academico", "is_staff")
    search_fields = ("email", "username", "dpi")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos de la plataforma de becas", {
            "fields": ("dpi", "telefono", "direccion", "rol", "nivel_academico")
        }),
    )
