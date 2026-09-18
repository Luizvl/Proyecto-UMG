from rest_framework.routers import DefaultRouter
from .views import ConvocatoriaViewSet

router = DefaultRouter()
router.register(r"convocatorias", ConvocatoriaViewSet, basename="convocatoria")

urlpatterns = router.urls
