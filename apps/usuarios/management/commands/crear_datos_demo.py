"""
Crea datos de prueba para ver el panel del estudiante con información:

    python manage.py crear_datos_demo

- Administrador: admin@becas.local / Admin12345  (entra a /admin/)
- Estudiante: estudiante@becas.local / Estudiante123
- 3 convocatorias abiertas
- 3 solicitudes: aprobada, con documentos pendientes y en evaluación
- 1 convocatoria abierta sin solicitud y 1 cerrada (para ver todos los estados)

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

        # Administrador con rol ADMINISTRADOR (createsuperuser lo deja como Estudiante)
        admin, _ = Usuario.objects.update_or_create(
            email="admin@becas.local",
            defaults={
                "username": "admin@becas.local",
                "first_name": "Administrador",
                "rol": Usuario.Rol.ADMINISTRADOR,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("Admin12345")
        admin.save()

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
            ("Beca Excelencia Universitaria", Convocatoria.TIPO_UNIVERSITARIO, "Para estudiantes con alto rendimiento académico."),
            ("Beca de Apoyo Económico", Convocatoria.TIPO_MEDIO, "Dirigida a estudiantes en situación de vulnerabilidad."),
            ("Beca de Posgrado", Convocatoria.TIPO_POSGRADO, "Para estudios de maestría y doctorado."),
        ]
        convocatorias = []
        for nombre, tipo, descripcion in nombres:
            c, _ = Convocatoria.objects.update_or_create(
                nombre=nombre,
                defaults={
                    "tipo_beca": tipo,
                    "descripcion": descripcion,
                    "fecha_inicio": hoy - timedelta(days=30),
                    "fecha_fin": hoy + timedelta(days=60),
                    "cupo": 20,
                    "estado": Convocatoria.ESTADO_ACTIVA,
                },
            )
            convocatorias.append(c)

        # Una abierta sin solicitud (muestra "Aplicar") y una cerrada (muestra "No disponible")
        Convocatoria.objects.update_or_create(
            nombre="Beca de Posgrado en Ciencias",
            defaults={"tipo_beca": Convocatoria.TIPO_POSGRADO,
                      "descripcion": "Apoyo para estudios de posgrado en áreas de investigación científica de interés nacional.",
                      "fecha_inicio": hoy - timedelta(days=15), "fecha_fin": hoy + timedelta(days=45),
                      "cupo": 10, "estado": Convocatoria.ESTADO_ACTIVA},
        )
        Convocatoria.objects.update_or_create(
            nombre="Beca Nivel Medio Rural (2025)",
            defaults={"tipo_beca": Convocatoria.TIPO_MEDIO,
                      "descripcion": "Convocatoria anterior, ya finalizada.",
                      "fecha_inicio": hoy - timedelta(days=300), "fecha_fin": hoy - timedelta(days=200),
                      "cupo": 15, "estado": Convocatoria.ESTADO_CERRADA},
        )

        # Solicitudes nuevas cada vez para que los datos queden limpios
        Solicitud.objects.filter(estudiante=estudiante).delete()
        ahora = timezone.now()

        def crear(convocatoria, estado, docs, dias_atras, historial=None):
            s = Solicitud.objects.create(estudiante=estudiante, convocatoria=convocatoria, estado=estado)
            Solicitud.objects.filter(pk=s.pk).update(fecha_creacion=ahora - timedelta(days=dias_atras))
            for tipo in docs:
                doc = Documento(solicitud=s, tipo=tipo)
                doc.archivo.save(f"{tipo.lower()}.pdf", ContentFile(b"%PDF-1.4 documento de prueba"), save=True)
                Documento.objects.filter(pk=doc.pk).update(fecha_carga=ahora - timedelta(days=dias_atras - 1))
            for anterior, nuevo, comentario, dias in (historial or []):
                h = HistorialEstado.objects.create(solicitud=s, estado_anterior=anterior, estado_nuevo=nuevo, comentario=comentario)
                HistorialEstado.objects.filter(pk=h.pk).update(fecha=ahora - timedelta(days=dias))
            return s

        # Se crean de la más antigua a la más reciente
        crear(convocatorias[2], Solicitud.APROBADA, ["DPI", "CONSTANCIA_ESTUDIOS", "NOTAS"], 40, [
            (Solicitud.PENDIENTE, Solicitud.EN_EVALUACION, "Estamos revisando la información de tu solicitud.", 35),
            (Solicitud.EN_EVALUACION, Solicitud.APROBADA, "¡Felicidades! Tu beca fue aprobada.", 20),
        ])
        crear(convocatorias[1], Solicitud.PENDIENTE, ["DPI"], 10)
        crear(convocatorias[0], Solicitud.EN_EVALUACION, ["DPI", "CONSTANCIA_ESTUDIOS"], 5, [
            (Solicitud.PENDIENTE, Solicitud.EN_EVALUACION, "Estamos revisando la información de tu solicitud.", 2),
        ])

        self.stdout.write(self.style.SUCCESS(
            "Datos de prueba listos.\n"
            "  Administrador: admin@becas.local / Admin12345\n"
            "  Estudiante:    estudiante@becas.local / Estudiante123"
        ))
