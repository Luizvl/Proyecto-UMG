from rest_framework import permissions, viewsets

from .models import Convocatoria
from .serializers import ConvocatoriaSerializer


class ConvocatoriaViewSet(viewsets.ModelViewSet):
    """
    list/retrieve: cualquier usuario autenticado (estudiantes incluidos, HU-03).
    create/update/delete: pensado para administradores (afinar permisos en Sprint 1 con HU-19).
    """
    queryset = Convocatoria.objects.all()
    serializer_class = ConvocatoriaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        activas = self.request.query_params.get("activas")
        if activas == "true":
            qs = qs.filter(estado=Convocatoria.ESTADO_ACTIVA)
        return qs
