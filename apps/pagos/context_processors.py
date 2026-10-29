from apps.usuarios.models import Usuario

from .services import estado_de_pagos


def estado_pagos(request):
    usuario = getattr(request, "user", None)
    if usuario is not None and usuario.is_authenticated and usuario.rol == Usuario.Rol.ESTUDIANTE:
        return estado_de_pagos(usuario)
    return {}