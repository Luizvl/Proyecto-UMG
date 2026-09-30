from rest_framework import serializers

from apps.usuarios.models import Usuario

from .models import Comite, Evaluacion


class ComiteSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Comite

        fields = [
            "id",
            "nombre",
            "convocatoria",
            "integrantes",
        ]

    def validate_integrantes(
        self,
        integrantes,
    ):
        for usuario in integrantes:
            if (
                usuario.rol
                != Usuario.Rol.COMITE
            ):
                raise serializers.ValidationError(
                    "Todos los integrantes deben "
                    "tener rol de Comité."
                )

        return integrantes


class EvaluacionSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Evaluacion

        fields = [
            "id",
            "solicitud",
            "evaluador",
            "puntaje",
            "comentario",
            "fecha",
        ]

        read_only_fields = [
            "evaluador",
            "fecha",
        ]

    def validate_puntaje(
        self,
        puntaje,
    ):
        if (
            puntaje < 0
            or puntaje > 100
        ):
            raise serializers.ValidationError(
                "El puntaje debe estar "
                "entre 0 y 100."
            )

        return puntaje