from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Módulos de la aplicación
    path('', include('apps.paginas.urls')),
    path('convocatorias/', include(('apps.convocatorias.urls_web', 'convocatorias'), namespace='convocatorias')),
    path('solicitudes/', include(('apps.solicitudes.urls_web', 'solicitudes'), namespace='solicitudes')),
    path('usuarios/', include(('apps.usuarios.urls', 'usuarios'), namespace='usuarios')),
]