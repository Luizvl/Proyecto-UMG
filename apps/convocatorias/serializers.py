from rest_framework import serializers
from .models import Convocatoria


class ConvocatoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convocatoria
        fields = ["id", "nombre", "tipo_beca", "descripcion", "fecha_inicio", "fecha_fin", "cupo", "estado"]

    def validate(self, data):
        inicio = data.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fin = data.get("fecha_fin", getattr(self.instance, "fecha_fin", None))
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError("La fecha fin no puede ser anterior a la fecha de inicio.")
        return data
