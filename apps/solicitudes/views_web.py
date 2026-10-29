from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.apps import apps

# ¡IMPORTANTE! Agregamos el modelo Documento a la importación
from .models import Solicitud, Documento 
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

            # CORRECCIÓN BUG #1: Usamos el estado oficial del modelo
            solicitud.estado = Solicitud.PENDIENTE 

            # Guardamos la solicitud principal en la base de datos
            solicitud.save()
            
            # (Opcional) Si el formulario es ModelForm y tiene ManyToMany
            if hasattr(form, 'save_m2m'):
                form.save_m2m()

            # CORRECCIÓN BUG #2: Guardar el PDF en la tabla correspondiente
            archivo_pdf = request.FILES.get('documento')
            if archivo_pdf:
                Documento.objects.create(
                    solicitud=solicitud,
                    tipo=Documento.TIPO_OTRO,  # O puedes poner Documento.TIPO_CONSTANCIA
                    archivo=archivo_pdf
                )

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