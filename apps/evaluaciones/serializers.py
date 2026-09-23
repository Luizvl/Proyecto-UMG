from rest_framework import serializers
from .models import Comite, Evaluacion


class ComiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comite
        fields = ["id", "nombre", "convocatoria", "integrantes"]


class EvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluacion
        fields = ["id", "solicitud", "evaluador", "puntaje", "comentario", "fecha"]
        read_only_fields = ["evaluador", "fecha"]
