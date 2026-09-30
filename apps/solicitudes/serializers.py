from pathlib import Path

from rest_framework import serializers

from .models import Documento, HistorialEstado, Solicitud


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento

        fields = [
            "id",
            "solicitud",
            "tipo",
            "archivo",
            "fecha_carga",
        ]

        read_only_fields = [
            "fecha_carga",
        ]

    def validate_archivo(self, archivo):
        """
        Valida extensión y tamaño del archivo.
        """

        extensiones_permitidas = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
        }

        extension = Path(
            archivo.name
        ).suffix.lower()

        if extension not in extensiones_permitidas:
            raise serializers.ValidationError(
                "Formato no permitido. "
                "Utilice PDF, JPG, JPEG o PNG."
            )

        maximo_bytes = 5 * 1024 * 1024

        if archivo.size > maximo_bytes:
            raise serializers.ValidationError(
                "El archivo no puede superar los 5 MB."
            )

        return archivo

    def validate(self, data):
        """
        Evita duplicar documentos principales.
        El tipo OTRO sí puede repetirse.
        """

        solicitud = data.get("solicitud")
        tipo = data.get("tipo")

        if (
            solicitud
            and tipo
            and tipo != Documento.TIPO_OTRO
        ):
            existe = Documento.objects.filter(
                solicitud=solicitud,
                tipo=tipo,
            ).exists()

            if existe:
                raise serializers.ValidationError(
                    {
                        "tipo": (
                            "Ya existe un documento de este "
                            "tipo para la solicitud."
                        )
                    }
                )

        return data


class HistorialEstadoSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = HistorialEstado

        fields = [
            "estado_anterior",
            "estado_nuevo",
            "fecha",
            "comentario",
        ]


class SolicitudSerializer(
    serializers.ModelSerializer
):
    documentos = DocumentoSerializer(
        many=True,
        read_only=True,
    )

    historial = HistorialEstadoSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Solicitud

        fields = [
            "id",
            "estudiante",
            "convocatoria",
            "estado",
            "motivo_rechazo",
            "fecha_creacion",
            "fecha_actualizacion",
            "documentos",
            "historial",
        ]

        read_only_fields = [
            "estado",
            "motivo_rechazo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]


class RechazarSolicitudSerializer(
    serializers.Serializer
):
    motivo = serializers.CharField(
        required=True,
        allow_blank=False,
    )