from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Solicitud
from .serializers import RechazarSolicitudSerializer, SolicitudSerializer
from .services import SolicitudService


class SolicitudViewSet(viewsets.ModelViewSet):
    """
    Expone el flujo de negocio de Solicitud a través de la Facade
    SolicitudService, en vez de manipular el modelo directamente.
    """
    queryset = Solicitud.objects.select_related("estudiante", "convocatoria").prefetch_related(
        "documentos", "historial"
    )
    serializer_class = SolicitudSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # La creación pasa por el service (Facade) para validar reglas de negocio
        # (convocatoria activa, no duplicar solicitud) en un solo lugar.
        from django.contrib.auth import get_user_model
        from apps.convocatorias.models import Convocatoria

        Usuario = get_user_model()
        estudiante = Usuario.objects.get(pk=request.data.get("estudiante"))
        convocatoria = Convocatoria.objects.get(pk=request.data.get("convocatoria"))
        try:
            solicitud = SolicitudService.crear_solicitud(estudiante, convocatoria)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(solicitud).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def iniciar_evaluacion(self, request, pk=None):
        solicitud = self.get_object()
        try:
            SolicitudService.iniciar_evaluacion(solicitud)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        solicitud = self.get_object()
        try:
            SolicitudService.aprobar(solicitud)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        solicitud = self.get_object()
        serializer = RechazarSolicitudSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            SolicitudService.rechazar(solicitud, serializer.validated_data["motivo"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(solicitud).data)
