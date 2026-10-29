from rest_framework.routers import DefaultRouter
from .views import ComiteViewSet, EvaluacionViewSet

router = DefaultRouter()
router.register(r"comites", ComiteViewSet, basename="comite")
router.register(r"evaluaciones", EvaluacionViewSet, basename="evaluacion")

urlpatterns = router.urls
