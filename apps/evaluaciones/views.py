from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.models import Usuario
from apps.usuarios.permissions import (
    EsAdministrador,
    EsComiteOAdministrador,
)

from .factories import EstrategiaEvaluacionFactory
from .models import Comite, Evaluacion
from .serializers import ComiteSerializer, EvaluacionSerializer


class ComiteViewSet(viewsets.ModelViewSet):
    """
    Gestión de comités evaluadores.

    - ADMINISTRADOR: puede crear, editar y eliminar comités.
    - COMITÉ: puede consultar únicamente los comités a los que pertenece.
    """

    queryset = Comite.objects.prefetch_related("integrantes").all()
    serializer_class = ComiteSerializer

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [EsAdministrador]
        else:
            permission_classes = [EsComiteOAdministrador]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if (
            usuario.is_authenticated
            and usuario.rol == Usuario.Rol.COMITE
            and not usuario.is_superuser
        ):
            qs = qs.filter(integrantes=usuario)

        return qs


class EvaluacionViewSet(viewsets.ModelViewSet):
    """
    Gestión de evaluaciones.

    - COMITÉ y ADMINISTRADOR pueden consultar evaluaciones.
    - COMITÉ solo puede consultar sus propias evaluaciones.
    - Al crear una evaluación, el evaluador será siempre
      el usuario autenticado.
    """

    queryset = Evaluacion.objects.select_related(
        "solicitud",
        "evaluador",
        "solicitud__convocatoria",
    ).all()

    serializer_class = EvaluacionSerializer

    def get_permissions(self):
        permission_classes = [EsComiteOAdministrador]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user

        if (
            usuario.is_authenticated
            and usuario.rol == Usuario.Rol.COMITE
            and not usuario.is_superuser
        ):
            qs = qs.filter(evaluador=usuario)

        return qs

    def create(self, request, *args, **kwargs):
        """
        El evaluador se obtiene del usuario autenticado.
        No se permite evaluar usando el ID de otro usuario.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        solicitud = serializer.validated_data["solicitud"]

        # Un miembro del comité solo puede evaluar solicitudes
        # de convocatorias para las que fue asignado.
        if (
            request.user.rol == Usuario.Rol.COMITE
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

        # Evita registrar dos evaluaciones del mismo usuario
        # para una misma solicitud.
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
            puntaje=serializer.validated_data["puntaje"],
            comentario=serializer.validated_data.get(
                "comentario",
                "",
            ),
        )

        return Response(
            self.get_serializer(evaluacion).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="puntaje-final/(?P<solicitud_id>[^/.]+)",
    )
    def puntaje_final(self, request, solicitud_id=None):
        """
        Calcula el puntaje final utilizando Factory + Strategy.
        """

        evaluaciones = Evaluacion.objects.filter(
            solicitud_id=solicitud_id
        ).select_related(
            "solicitud__convocatoria"
        )

        if not evaluaciones.exists():
            return Response(
                {
                    "detail": (
                        "La solicitud no tiene evaluaciones "
                        "registradas."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        tipo_beca = (
            evaluaciones.first()
            .solicitud.convocatoria.tipo_beca
        )

        estrategia = EstrategiaEvaluacionFactory.crear(
            tipo_beca
        )

        puntajes = [
            float(evaluacion.puntaje)
            for evaluacion in evaluaciones
        ]

        resultado = estrategia.calcular_puntaje_final(
            puntajes
        )

        return Response(
            {
                "solicitud_id": solicitud_id,
                "puntaje_final": resultado,
                "estrategia": estrategia.__class__.__name__,
            }
        )