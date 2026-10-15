"""
Crea datos de prueba para ver el panel del estudiante con información:

    python manage.py crear_datos_demo

- Estudiante: estudiante@becas.local / Estudiante123
- 3 convocatorias abiertas
- 1 solicitud "En evaluación" con 2 de 3 documentos y su historial

Solo para desarrollo local. Se puede ejecutar varias veces.
"""
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.convocatorias.models import Convocatoria
from apps.solicitudes.models import Documento, HistorialEstado, Solicitud
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea un estudiante con una solicitud de ejemplo para probar el panel."

    def handle(self, *args, **options):
        hoy = timezone.localdate()

        estudiante, _ = Usuario.objects.update_or_create(
            email="estudiante@becas.local",
            defaults={
                "username": "estudiante@becas.local",
                "first_name": "Enrique",
                "last_name": "Demo",
                "rol": Usuario.Rol.ESTUDIANTE,
                "nivel_academico": Usuario.NivelAcademico.UNIVERSITARIO,
            },
        )
        estudiante.set_password("Estudiante123")
        estudiante.save()

        nombres = [
            ("Beca Excelencia Universitaria", Convocatoria.TIPO_UNIVERSITARIO),
            ("Beca Nivel Medio Rural", Convocatoria.TIPO_MEDIO),
            ("Beca de Posgrado en Ciencias", Convocatoria.TIPO_POSGRADO),
        ]
        convocatorias = []
        for nombre, tipo in nombres:
            c, _ = Convocatoria.objects.update_or_create(
                nombre=nombre,
                defaults={
                    "tipo_beca": tipo,
                    "descripcion": "Convocatoria de ejemplo para pruebas.",
                    "fecha_inicio": hoy - timedelta(days=30),
                    "fecha_fin": hoy + timedelta(days=60),
                    "cupo": 20,
                    "estado": Convocatoria.ESTADO_ACTIVA,
                },
            )
            convocatorias.append(c)

        # Solicitud nueva cada vez para que los datos queden limpios
        Solicitud.objects.filter(estudiante=estudiante).delete()
        solicitud = Solicitud.objects.create(
            estudiante=estudiante,
            convocatoria=convocatorias[0],
            estado=Solicitud.EN_EVALUACION,
        )

        for tipo, nombre in [("DPI", "dpi.pdf"), ("CONSTANCIA_ESTUDIOS", "constancia.pdf")]:
            doc = Documento(solicitud=solicitud, tipo=tipo)
            doc.archivo.save(nombre, ContentFile(b"%PDF-1.4 documento de prueba"), save=True)

        HistorialEstado.objects.create(
            solicitud=solicitud,
            estado_anterior=Solicitud.PENDIENTE,
            estado_nuevo=Solicitud.EN_EVALUACION,
            comentario="Estamos revisando la información de tu solicitud.",
        )

        self.stdout.write(self.style.SUCCESS(
            "Datos de prueba listos. Entra con estudiante@becas.local / Estudiante123"
        ))
