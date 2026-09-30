from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.solicitudes.models import Solicitud
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import (
    EsAdministrador,
    EsComiteOAdministrador,
)

from .factories import EstrategiaEvaluacionFactory
from .models import Comite, Evaluacion
from .serializers import (
    ComiteSerializer,
    EvaluacionSerializer,
)


class ComiteViewSet(viewsets.ModelViewSet):
    """
    Gestión de comités evaluadores.

    ADMINISTRADOR:
    - Puede crear, editar y eliminar comités.
    - Puede consultar todos los comités.

    COMITÉ:
    - Solo puede consultar los comités
      a los que pertenece.
    """

    queryset = Comite.objects.select_related(
        "convocatoria"
    ).prefetch_related(
        "integrantes"
    )

    serializer_class = ComiteSerializer

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [
                EsAdministrador
            ]

        else:
            permission_classes = [
                EsComiteOAdministrador
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if not usuario.is_authenticated:
            return qs.none()

        if (
            usuario.rol == Usuario.Rol.COMITE
            and not usuario.is_superuser
        ):
            return qs.filter(
                integrantes=usuario
            )

        return qs


class EvaluacionViewSet(viewsets.ModelViewSet):
    """
    Gestión de evaluaciones.

    COMITÉ:
    - Puede evaluar únicamente solicitudes
      de convocatorias donde está asignado.
    - Solo puede consultar sus propias evaluaciones.

    ADMINISTRADOR:
    - Puede consultar todas las evaluaciones.
    - Puede registrar evaluaciones.

    REGLAS:
    - Solo se evalúan solicitudes EN_EVALUACION.
    - Un evaluador solo puede evaluar una vez
      cada solicitud.
    - El puntaje debe estar entre 0 y 100.
    """

    queryset = Evaluacion.objects.select_related(
        "solicitud",
        "evaluador",
        "solicitud__convocatoria",
        "solicitud__estudiante",
    )

    serializer_class = EvaluacionSerializer

    def get_permissions(self):
        permission_classes = [
            EsComiteOAdministrador
        ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if not usuario.is_authenticated:
            return qs.none()

        if (
            usuario.rol == Usuario.Rol.COMITE
            and not usuario.is_superuser
        ):
            return qs.filter(
                evaluador=usuario
            )

        return qs

    def create(self, request, *args, **kwargs):
        """
        Registra una evaluación.

        El evaluador se obtiene siempre del usuario
        autenticado y nunca del JSON enviado.
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

        # Solo se puede evaluar una solicitud
        # que ya se encuentra EN_EVALUACION.
        if (
            solicitud.estado
            != Solicitud.EN_EVALUACION
        ):
            return Response(
                {
                    "detail": (
                        "La solicitud debe estar en estado "
                        "'En Evaluación' para registrar "
                        "una evaluación."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Si es miembro del comité, se valida que
        # realmente pertenezca al comité asignado
        # a la convocatoria.
        if (
            request.user.rol
            == Usuario.Rol.COMITE
            and not request.user.is_superuser
        ):
            pertenece = Comite.objects.filter(
                convocatoria=solicitud.convocatoria,
                integrantes=request.user,
            ).exists()

            if not pertenece:
                return Response(
                    {
                        "detail": (
                            "No pertenece al comité asignado "
                            "a esta convocatoria."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Evitar evaluación duplicada.
        if Evaluacion.objects.filter(
            solicitud=solicitud,
            evaluador=request.user,
        ).exists():
            return Response(
                {
                    "detail": (
                        "Ya existe una evaluación realizada "
                        "por este usuario para esta solicitud."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        evaluacion = Evaluacion.objects.create(
            solicitud=solicitud,
            evaluador=request.user,
            puntaje=serializer.validated_data[
                "puntaje"
            ],
            comentario=serializer.validated_data.get(
                "comentario",
                "",
            ),
        )

        return Response(
            self.get_serializer(
                evaluacion
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path=(
            "puntaje-final/"
            "(?P<solicitud_id>[^/.]+)"
        ),
    )
    def puntaje_final(
        self,
        request,
        solicitud_id=None,
    ):
        """
        Calcula el puntaje final utilizando
        Factory + Strategy.
        """

        try:
            solicitud = (
                Solicitud.objects
                .select_related(
                    "convocatoria"
                )
                .get(
                    pk=solicitud_id
                )
            )

        except Solicitud.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "La solicitud no existe."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Comité:
        # solo puede calcular el puntaje de
        # convocatorias a las que pertenece.
        if (
            request.user.rol
            == Usuario.Rol.COMITE
            and not request.user.is_superuser
        ):
            pertenece = Comite.objects.filter(
                convocatoria=solicitud.convocatoria,
                integrantes=request.user,
            ).exists()

            if not pertenece:
                return Response(
                    {
                        "detail": (
                            "No tiene acceso a esta "
                            "solicitud."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        evaluaciones = Evaluacion.objects.filter(
            solicitud=solicitud
        )

        if not evaluaciones.exists():
            return Response(
                {
                    "detail": (
                        "La solicitud no tiene "
                        "evaluaciones registradas."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        estrategia = (
            EstrategiaEvaluacionFactory.crear(
                solicitud.convocatoria.tipo_beca
            )
        )

        puntajes = [
            float(evaluacion.puntaje)
            for evaluacion in evaluaciones
        ]

        resultado = (
            estrategia.calcular_puntaje_final(
                puntajes
            )
        )

        return Response(
            {
                "solicitud_id": solicitud.id,
                "puntaje_final": resultado,
                "cantidad_evaluaciones": (
                    evaluaciones.count()
                ),
                "estrategia": (
                    estrategia
                    .__class__
                    .__name__
                ),
            },
            status=status.HTTP_200_OK,
        )