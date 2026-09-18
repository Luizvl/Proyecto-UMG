"""
Enrutador principal del proyecto.
Cada app expone sus propias rutas bajo /api/, manteniendo la
separación por dominio (capa de presentación distribuida).
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.convocatorias.urls")),
    path("api/", include("apps.solicitudes.urls")),
    path("api/", include("apps.evaluaciones.urls")),
    path("api-auth/", include("rest_framework.urls")),  # login/logout navegable de DRF
    path("usuarios/", include("apps.usuarios.urls")),  # pantallas web (registro, etc.)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
