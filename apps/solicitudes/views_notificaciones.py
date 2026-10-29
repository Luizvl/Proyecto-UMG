from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionViewSet(
    viewsets.ReadOnlyModelViewSet
):
    """
    Permite al usuario autenticado consultar
    únicamente sus propias notificaciones.

    También permite marcar una notificación
    como leída.
    """

    serializer_class = NotificacionSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        """
        Cada usuario únicamente puede consultar
        sus propias notificaciones.
        """

        return Notificacion.objects.filter(
            destinatario=self.request.user
        ).select_related(
            "solicitud",
            "destinatario",
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="marcar-leida",
    )
    def marcar_leida(
        self,
        request,
        pk=None,
    ):
        """
        Marca una notificación como leída.
        """

        notificacion = self.get_object()

        if not notificacion.leida:
            notificacion.leida = True

            notificacion.save(
                update_fields=[
                    "leida",
                ]
            )

        return Response(
            self.get_serializer(
                notificacion
            ).data,
            status=status.HTTP_200_OK,
        )