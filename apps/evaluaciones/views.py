from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .factories import EstrategiaEvaluacionFactory
from .models import Comite, Evaluacion
from .serializers import ComiteSerializer, EvaluacionSerializer


class ComiteViewSet(viewsets.ModelViewSet):
    queryset = Comite.objects.prefetch_related("integrantes").all()
    serializer_class = ComiteSerializer
    permission_classes = [permissions.IsAuthenticated]


class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.select_related("solicitud", "evaluador").all()
    serializer_class = EvaluacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="puntaje-final/(?P<solicitud_id>[^/.]+)")
    def puntaje_final(self, request, solicitud_id=None):
        """
        Calcula el puntaje final de una solicitud usando la estrategia
        correspondiente al tipo de beca (Factory Method + Strategy).
        """
        evaluaciones = Evaluacion.objects.filter(solicitud_id=solicitud_id)
        if not evaluaciones.exists():
            return Response({"detail": "La solicitud no tiene evaluaciones registradas."}, status=404)

        tipo_beca = evaluaciones.first().solicitud.convocatoria.tipo_beca
        estrategia = EstrategiaEvaluacionFactory.crear(tipo_beca)
        puntajes = [float(e.puntaje) for e in evaluaciones]
        resultado = estrategia.calcular_puntaje_final(puntajes)
        return Response({"solicitud_id": solicitud_id, "puntaje_final": resultado, "estrategia": estrategia.__class__.__name__})
