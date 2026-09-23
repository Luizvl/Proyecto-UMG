from rest_framework import permissions, viewsets

from apps.usuarios.permissions import EsAdministrador

from .models import Convocatoria
from .serializers import ConvocatoriaSerializer


class ConvocatoriaViewSet(viewsets.ModelViewSet):
    """
    Gestión de convocatorias.

    - Cualquier usuario autenticado puede consultar convocatorias.
    - Solo un administrador puede crear, modificar o eliminar convocatorias.
    """

    queryset = Convocatoria.objects.all()
    serializer_class = ConvocatoriaSerializer

    def get_permissions(self):
        """
        Define permisos dependiendo de la acción solicitada.
        """

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [EsAdministrador]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        qs = super().get_queryset()

        activas = self.request.query_params.get("activas")

        if activas == "true":
            qs = qs.filter(
                estado=Convocatoria.ESTADO_ACTIVA
            )

        return qs