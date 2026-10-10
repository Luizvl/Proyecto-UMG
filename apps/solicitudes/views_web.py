from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.apps import apps

from .models import Solicitud
from .forms import SolicitudForm


def obtener_modelo_convocatoria():
    return apps.get_model('convocatorias', 'Convocatoria')


@login_required
def aplicar_convocatoria(request, convocatoria_id):
    Convocatoria = obtener_modelo_convocatoria()
    convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)
    usuario_actual = request.user

    # 1. Validar si el usuario ya envió una solicitud para esta convocatoria
    if Solicitud.objects.filter(estudiante=usuario_actual, convocatoria=convocatoria).exists():
        messages.warning(request, "Ya has enviado una solicitud para esta convocatoria.")
        return redirect('solicitudes:panel_estudiante')

    # 2. Procesamiento del formulario y archivo adjunto
    if request.method == 'POST':
        form = SolicitudForm(request.POST, request.FILES)
        if form.is_valid():
            solicitud = form.save(commit=False)
            
            # Asignación explícita de campos obligatorios
            solicitud.estudiante = usuario_actual
            solicitud.convocatoria = convocatoria

            # Asignación del estado borrador si existe el campo
            if hasattr(Solicitud, 'Estado') and hasattr(Solicitud.Estado, 'BORRADOR'):
                solicitud.estado = Solicitud.Estado.BORRADOR
            elif hasattr(solicitud, 'estado'):
                solicitud.estado = 'BORRADOR'

            solicitud.save()
            form.save_m2m()

            messages.success(request, "¡Tu solicitud ha sido enviada exitosamente!")
            return redirect('solicitudes:panel_estudiante')
        else:
            messages.error(request, "Ocurrió un error al validar los datos del formulario.")
    else:
        form = SolicitudForm()

    contexto = {
        'convocatoria': convocatoria,
        'form': form
    }
    return render(request, 'solicitudes/aplicar.html', contexto)


@login_required
def panel_estudiante(request):
    usuario_actual = request.user
    solicitudes = Solicitud.objects.filter(estudiante=usuario_actual).select_related('convocatoria')

    contexto = {
        'solicitudes': solicitudes,
        'usuario': usuario_actual,
    }
    return render(request, 'solicitudes/mis_solicitudes.html', contexto)

  