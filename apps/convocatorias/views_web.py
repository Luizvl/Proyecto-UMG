from django.shortcuts import render
from .models import Convocatoria
from apps.solicitudes.models import Solicitud

def listado_convocatorias(request):
    # Carga TODAS las convocatorias creadas sin filtrar por estado
    convocatorias = Convocatoria.objects.all()
    
    aplicadas_ids = []
    # CORRECCIÓN: Quitamos el hasattr y usamos request.user directamente
    if request.user.is_authenticated:
        aplicadas_ids = Solicitud.objects.filter(
            estudiante=request.user
        ).values_list('convocatoria_id', flat=True)

    contexto = {
        'convocatorias': convocatorias,
        'aplicadas_ids': aplicadas_ids,
    }
    return render(request, 'convocatorias/listado.html', contexto)