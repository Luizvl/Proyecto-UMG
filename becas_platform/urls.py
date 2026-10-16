from django.contrib import admin
from django.urls import path, include

# 1. Agregamos estas dos importaciones vitales
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Módulos de la aplicación
    path('', include('apps.paginas.urls')),
    path('convocatorias/', include(('apps.convocatorias.urls_web', 'convocatorias'), namespace='convocatorias')),
    path('solicitudes/', include(('apps.solicitudes.urls_web', 'solicitudes'), namespace='solicitudes')),
    path('usuarios/', include(('apps.usuarios.urls', 'usuarios'), namespace='usuarios')),
]

# 2. Agregamos el puente para los archivos multimedia en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)