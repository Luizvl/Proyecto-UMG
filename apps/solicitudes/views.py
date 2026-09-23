from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.convocatorias.models import Convocatoria
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import (
    EsAdministrador,
    EsComiteOAdministrador,
    EsEstudianteOAdministrador,
)

from .models import Solicitud
from .serializers import RechazarSolicitudSerializer, SolicitudSerializer
from .services import SolicitudService


class SolicitudViewSet(viewsets.ModelViewSet):
    """
    Gestión de solicitudes de beca.

    ESTUDIANTE:
    - Puede crear solicitudes a su propio nombre.
    - Solo puede consultar sus propias solicitudes.

    COMITÉ:
    - Puede consultar solicitudes.
    - Puede iniciar evaluación, aprobar o rechazar.

    ADMINISTRADOR:
    - Puede consultar todas las solicitudes.
    - Puede crear solicitudes para estudiantes.
    - Puede administrar y procesar solicitudes.
    """

    queryset = Solicitud.objects.select_related(
        "estudiante",
        "convocatoria",
    ).prefetch_related(
        "documentos",
        "historial",
    )

    serializer_class = SolicitudSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [EsEstudianteOAdministrador]

        elif self.action in [
            "iniciar_evaluacion",
            "aprobar",
            "rechazar",
        ]:
            permission_classes = [EsComiteOAdministrador]

        elif self.action in [
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [EsAdministrador]

        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Los estudiantes solo pueden ver sus propias solicitudes.
        Comité y administrador pueden ver todas.
        """

        qs = super().get_queryset()
        usuario = self.request.user

        if (
            usuario.is_authenticated
            and usuario.rol == Usuario.Rol.ESTUDIANTE
            and not usuario.is_superuser
        ):
            qs = qs.filter(estudiante=usuario)

        return qs

    def create(self, request, *args, **kwargs):
        """
        Si quien crea es estudiante, la solicitud queda automáticamente
        asociada al usuario autenticado.

        Si es administrador, puede indicar el estudiante mediante su ID.
        """

        UsuarioModel = get_user_model()

        if (
            request.user.rol == Usuario.Rol.ESTUDIANTE
            and not request.user.is_superuser
        ):
            estudiante = request.user

        else:
            estudiante_id = request.data.get("estudiante")

            if not estudiante_id:
                return Response(
                    {
                        "detail": (
                            "Debe indicar el estudiante para crear "
                            "la solicitud."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            estudiante = get_object_or_404(
                UsuarioModel,
                pk=estudiante_id,
            )

            if estudiante.rol != Usuario.Rol.ESTUDIANTE:
                return Response(
                    {
                        "detail": (
                            "El usuario seleccionado no tiene rol "
                            "de estudiante."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        convocatoria_id = request.data.get("convocatoria")

        if not convocatoria_id:
            return Response(
                {"detail": "Debe indicar una convocatoria."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        convocatoria = get_object_or_404(
            Convocatoria,
            pk=convocatoria_id,
        )

        try:
            solicitud = SolicitudService.crear_solicitud(
                estudiante,
                convocatoria,
            )

        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(solicitud).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def iniciar_evaluacion(self, request, pk=None):
        solicitud = self.get_object()

        try:
            SolicitudService.iniciar_evaluacion(solicitud)

        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(solicitud).data
        )

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        solicitud = self.get_object()

        try:
            SolicitudService.aprobar(solicitud)

        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(solicitud).data
        )

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        solicitud = self.get_object()

        serializer = RechazarSolicitudSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        try:
            SolicitudService.rechazar(
                solicitud,
                serializer.validated_data["motivo"],
            )

        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(solicitud).data
        )