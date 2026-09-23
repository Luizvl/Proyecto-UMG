from rest_framework import serializers
from .models import Documento, HistorialEstado, Solicitud


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ["id", "solicitud", "tipo", "archivo", "fecha_carga"]
        read_only_fields = ["fecha_carga"]


class HistorialEstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialEstado
        fields = ["estado_anterior", "estado_nuevo", "fecha", "comentario"]


class SolicitudSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True, read_only=True)
    historial = HistorialEstadoSerializer(many=True, read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            "id", "estudiante", "convocatoria", "estado", "motivo_rechazo",
            "fecha_creacion", "fecha_actualizacion", "documentos", "historial",
        ]
        read_only_fields = ["estado", "motivo_rechazo", "fecha_creacion", "fecha_actualizacion"]


class RechazarSolicitudSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=True, allow_blank=False)
