from django.shortcuts import render

from apps.pagos.services import estado_de_pagos
from apps.usuarios.models import Usuario


def inicio(request):
    contexto = {}
    # Solo los estudiantes ven el aviso de pago
    if request.user.is_authenticated and request.user.rol == Usuario.Rol.ESTUDIANTE:
        contexto.update(estado_de_pagos(request.user))
    return render(request, "paginas/inicio.html", contexto)


def como_funciona(request):
    return render(request, "paginas/como_funciona.html")

def conocenos(request):
    return render(request, 'paginas/conocenos.html')