from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            "Información del proyecto",
            {
                "fields": (
                    "rol",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Información del proyecto",
            {
                "fields": (
                    "email",
                    "rol",
                )
            },
        ),
    )

    list_display = (
         "username",
    "email",
    "dpi",
    "rol",
    "is_active",
    "is_staff",
    )