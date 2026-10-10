from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.convocatorias.models import Convocatoria
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import (
    EsAdministrador,
    EsComiteOAdministrador,
    EsEstudianteOAdministrador,
)

from .models import Documento, Solicitud
from .serializers import (
    DocumentoSerializer,
    RechazarSolicitudSerializer,
    SolicitudSerializer,
)
from .services import SolicitudService


class SolicitudViewSet(viewsets.ModelViewSet):
    """
    Gestión de solicitudes de beca.

    ESTUDIANTE:
    - Puede crear solicitudes a su propio nombre.
    - Solo puede consultar sus propias solicitudes.

    COMITÉ:
    - Solo puede consultar solicitudes de convocatorias
      donde pertenece a un comité.
    - Puede iniciar evaluación, aprobar o rechazar
      únicamente esas solicitudes.

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
            permission_classes = [
                EsEstudianteOAdministrador
            ]

        elif self.action in [
            "iniciar_evaluacion",
            "aprobar",
            "rechazar",
        ]:
            permission_classes = [
                EsComiteOAdministrador
            ]

        elif self.action in [
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [
                EsAdministrador
            ]

        else:
            permission_classes = [
                permissions.IsAuthenticated
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        """
        Filtra las solicitudes según el rol del usuario.
        """

        qs = super().get_queryset()
        usuario = self.request.user

        if not usuario.is_authenticated:
            return qs.none()

        # Estudiante: solo sus propias solicitudes
        if (
            usuario.rol == Usuario.Rol.ESTUDIANTE
            and not usuario.is_superuser
        ):
            return qs.filter(
                estudiante=usuario
            )

        # Comité: solo solicitudes de convocatorias
        # donde pertenece al comité
        if (
            usuario.rol == Usuario.Rol.COMITE
            and not usuario.is_superuser
        ):
            return qs.filter(
                convocatoria__comites__integrantes=usuario
            ).distinct()

        # Administrador / superusuario: todas
        return qs

    def create(self, request, *args, **kwargs):
        """
        Crea una solicitud.

        Si el usuario es estudiante, se utiliza
        automáticamente el usuario autenticado.

        Si es administrador, debe indicar el estudiante.
        """

        UsuarioModel = get_user_model()

        if (
            request.user.rol == Usuario.Rol.ESTUDIANTE
            and not request.user.is_superuser
        ):
            estudiante = request.user

        else:
            estudiante_id = request.data.get(
                "estudiante"
            )

            if not estudiante_id:
                return Response(
                    {
                        "detail": (
                            "Debe indicar el estudiante "
                            "para crear la solicitud."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            estudiante = get_object_or_404(
                UsuarioModel,
                pk=estudiante_id,
            )

            if (
                estudiante.rol
                != Usuario.Rol.ESTUDIANTE
            ):
                return Response(
                    {
                        "detail": (
                            "El usuario seleccionado "
                            "no tiene rol de estudiante."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        convocatoria_id = request.data.get(
            "convocatoria"
        )

        if not convocatoria_id:
            return Response(
                {
                    "detail": (
                        "Debe indicar una convocatoria."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        convocatoria = get_object_or_404(
            Convocatoria,
            pk=convocatoria_id,
        )

        try:
            solicitud = (
                SolicitudService.crear_solicitud(
                    estudiante,
                    convocatoria,
                )
            )

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(
                solicitud
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def iniciar_evaluacion(
        self,
        request,
        pk=None,
    ):
        """
        Cambia:
        PENDIENTE -> EN_EVALUACION
        """

        solicitud = self.get_object()

        try:
            SolicitudService.iniciar_evaluacion(
                solicitud
            )

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(
                solicitud
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def aprobar(
        self,
        request,
        pk=None,
    ):
        """
        Aprueba una solicitud en evaluación.
        """

        solicitud = self.get_object()

        try:
            SolicitudService.aprobar(
                solicitud
            )

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(
                solicitud
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def rechazar(
        self,
        request,
        pk=None,
    ):
        """
        Rechaza una solicitud en evaluación.
        Requiere indicar un motivo.
        """

        solicitud = self.get_object()

        serializer = RechazarSolicitudSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            SolicitudService.rechazar(
                solicitud,
                serializer.validated_data[
                    "motivo"
                ],
            )

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(
                solicitud
            ).data
        )


class DocumentoViewSet(viewsets.ModelViewSet):
    """
    Gestión de documentos de las solicitudes.

    ESTUDIANTE:
    - Puede ver documentos de sus solicitudes.
    - Puede subir documentos a sus solicitudes.
    - Puede eliminarlos mientras la solicitud
      esté PENDIENTE.

    COMITÉ:
    - Puede consultar documentos de solicitudes
      correspondientes a convocatorias asignadas.

    ADMINISTRADOR:
    - Puede consultar, subir y eliminar documentos.
    """

    queryset = Documento.objects.select_related(
        "solicitud",
        "solicitud__estudiante",
        "solicitud__convocatoria",
    )

    serializer_class = DocumentoSerializer

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    # No permitimos PUT ni PATCH para documentos.
    http_method_names = [
        "get",
        "post",
        "delete",
        "head",
        "options",
    ]

    def get_permissions(self):
        """
        Estudiante y administrador pueden crear/eliminar.
        Los usuarios autenticados permitidos pueden consultar.
        """

        if self.action in [
            "create",
            "destroy",
        ]:
            permission_classes = [
                EsEstudianteOAdministrador
            ]

        else:
            permission_classes = [
                permissions.IsAuthenticated
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        """
        Filtra los documentos según el rol.
        """

        qs = super().get_queryset()
        usuario = self.request.user

        if not usuario.is_authenticated:
            return qs.none()

        # Estudiante:
        # únicamente documentos de sus solicitudes.
        if (
            usuario.rol == Usuario.Rol.ESTUDIANTE
            and not usuario.is_superuser
        ):
            return qs.filter(
                solicitud__estudiante=usuario
            )

        # Comité:
        # documentos únicamente de convocatorias
        # en las que participa.
        if (
            usuario.rol == Usuario.Rol.COMITE
            and not usuario.is_superuser
        ):
            return qs.filter(
                solicitud__convocatoria__comites__integrantes=usuario
            ).distinct()

        # Administrador:
        # todos los documentos.
        return qs

    def create(self, request, *args, **kwargs):
        """
        Carga un nuevo documento.
        """

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        solicitud = serializer.validated_data[
            "solicitud"
        ]

        # Un estudiante no puede subir documentos
        # a solicitudes de otras personas.
        if (
            request.user.rol
            == Usuario.Rol.ESTUDIANTE
            and not request.user.is_superuser
        ):
            if (
                solicitud.estudiante_id
                != request.user.id
            ):
                return Response(
                    {
                        "detail": (
                            "No puede agregar documentos "
                            "a una solicitud de otro estudiante."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Solo se permiten documentos mientras
        # la solicitud esté pendiente.
        if solicitud.estado != Solicitud.PENDIENTE:
            return Response(
                {
                    "detail": (
                        "Solo se pueden agregar documentos "
                        "mientras la solicitud esté pendiente."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        documento = SolicitudService.agregar_documento(
            solicitud=solicitud,
            archivo=serializer.validated_data[
                "archivo"
            ],
            tipo=serializer.validated_data[
                "tipo"
            ],
        )

        return Response(
            self.get_serializer(
                documento
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        """
        Elimina un documento mientras la solicitud
        permanezca en estado PENDIENTE.
        """

        documento = self.get_object()
        solicitud = documento.solicitud

        if (
            solicitud.estado
            != Solicitud.PENDIENTE
        ):
            return Response(
                {
                    "detail": (
                        "No se pueden eliminar documentos "
                        "cuando la solicitud ya está "
                        "en evaluación o finalizada."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        archivo = documento.archivo

        documento.delete()

        # Elimina también el archivo físico almacenado.
        if archivo:
            archivo.delete(
                save=False
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )