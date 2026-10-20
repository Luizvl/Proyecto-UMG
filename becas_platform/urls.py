from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Administración
    path(
        "admin/",
        admin.site.urls,
    ),

    # Páginas públicas
    path(
        "",
        include("apps.paginas.urls"),
    ),

    # Frontend web
    path(
        "convocatorias/",
        include(
            (
                "apps.convocatorias.urls_web",
                "convocatorias",
            ),
            namespace="convocatorias",
        ),
    ),
    path(
        "solicitudes/",
        include(
            (
                "apps.solicitudes.urls_web",
                "solicitudes",
            ),
            namespace="solicitudes",
        ),
    ),
    path(
        "usuarios/",
        include(
            (
                "apps.usuarios.urls",
                "usuarios",
            ),
            namespace="usuarios",
        ),
    ),

    # API REST
    path(
        "api/",
        include("apps.convocatorias.urls"),
    ),
    path(
        "api/",
        include("apps.solicitudes.urls"),
    ),
    path(
        "api/",
        include("apps.evaluaciones.urls"),
    ),

    # Autenticación navegable de DRF
    path(
        "api-auth/",
        include("rest_framework.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )