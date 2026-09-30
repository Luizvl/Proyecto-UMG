from rest_framework.routers import DefaultRouter

from .views import DocumentoViewSet, SolicitudViewSet


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


urlpatterns = router.urls