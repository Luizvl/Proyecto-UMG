from rest_framework.routers import DefaultRouter

from .views import (
    DocumentoViewSet,
    SolicitudViewSet,
)
from .views_notificaciones import (
    NotificacionViewSet,
)


router = DefaultRouter()

router.register(
    r"solicitudes",
    SolicitudViewSet,
    basename="solicitud",
)

router.register(
    r"documentos",
    DocumentoViewSet,
    basename="documento",
)

router.register(
    r"notificaciones",
    NotificacionViewSet,
    basename="notificacion",
)


urlpatterns = router.urls