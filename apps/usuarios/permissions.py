from rest_framework.permissions import BasePermission

from .models import Usuario


class EsEstudiante(BasePermission):
    """
    Permite acceso únicamente a usuarios con rol ESTUDIANTE.
    """

    message = "Esta acción está disponible únicamente para estudiantes."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == Usuario.Rol.ESTUDIANTE
        )


class EsComite(BasePermission):
    """
    Permite acceso únicamente a miembros del comité.
    """

    message = "Esta acción está disponible únicamente para miembros del comité."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == Usuario.Rol.COMITE
        )


class EsAdministrador(BasePermission):
    """
    Permite acceso a administradores del sistema.
    También reconoce al superusuario de Django como administrador.
    """

    message = "Esta acción está disponible únicamente para administradores."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.rol == Usuario.Rol.ADMINISTRADOR
                or request.user.is_superuser
            )
        )

class EsEstudianteOAdministrador(BasePermission):
    """
    Permite acceso a estudiantes o administradores.
    """

    message = "Esta acción requiere ser estudiante o administrador."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.rol == Usuario.Rol.ESTUDIANTE
                or request.user.rol == Usuario.Rol.ADMINISTRADOR
                or request.user.is_superuser
            )
        )
class EsComiteOAdministrador(BasePermission):
    """
    Permite acceso a miembros del comité o administradores.
    """

    message = "Esta acción requiere ser miembro del comité o administrador."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.rol == Usuario.Rol.COMITE
                or request.user.rol == Usuario.Rol.ADMINISTRADOR
                or request.user.is_superuser
            )


        )
