import tempfile

from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.convocatorias.models import Convocatoria
from apps.evaluaciones.models import Comite
from apps.usuarios.models import Usuario

from .models import Documento, Solicitud


class SolicitudAPITests(APITestCase):

    def setUp(self):
        self.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            email="estudiante1@test.com",
            password="Prueba12345",
            dpi="1234567890101",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.otro_estudiante = Usuario.objects.create_user(
            username="estudiante2",
            email="estudiante2@test.com",
            password="Prueba12345",
            dpi="1234567890102",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.comite = Usuario.objects.create_user(
            username="comite1",
            email="comite@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.COMITE,
        )

        self.convocatoria = Convocatoria.objects.create(
            nombre="Beca Universitaria 2026",
            tipo_beca="UNIVERSITARIO",
            descripcion="Convocatoria de prueba",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.comite_evaluador = Comite.objects.create(
            nombre="Comité Universitario",
            convocatoria=self.convocatoria,
        )

        self.comite_evaluador.integrantes.add(
            self.comite
        )

    def test_estudiante_crea_solicitud_a_su_nombre(self):
        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("solicitud-list"),
            {
                "estudiante": self.otro_estudiante.id,
                "convocatoria": self.convocatoria.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        solicitud = Solicitud.objects.get()

        self.assertEqual(
            solicitud.estudiante,
            self.estudiante,
        )

        self.assertNotEqual(
            solicitud.estudiante,
            self.otro_estudiante,
        )

    def test_estudiante_solo_ve_sus_solicitudes(self):
        solicitud_propia = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        otra_convocatoria = Convocatoria.objects.create(
            nombre="Segunda convocatoria",
            tipo_beca="UNIVERSITARIO",
            descripcion="Otra convocatoria",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        Solicitud.objects.create(
            estudiante=self.otro_estudiante,
            convocatoria=otra_convocatoria,
        )

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.get(
            reverse("solicitud-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            solicitud_propia.id,
        )

    def test_comite_puede_iniciar_y_aprobar_solicitud(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        self.client.force_authenticate(
            user=self.comite
        )

        response = self.client.post(
            reverse(
                "solicitud-iniciar-evaluacion",
                args=[solicitud.id],
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        solicitud.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            Solicitud.EN_EVALUACION,
        )

        response = self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud.id],
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        solicitud.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            Solicitud.APROBADA,
        )

    def test_estudiante_no_puede_aprobar_solicitud(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        solicitud.iniciar_evaluacion()

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud.id],
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_comite_no_puede_ver_solicitud_no_asignada(self):
        otra_convocatoria = Convocatoria.objects.create(
            nombre="Convocatoria no asignada",
            tipo_beca="UNIVERSITARIO",
            descripcion="Prueba de seguridad",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=otra_convocatoria,
        )

        self.client.force_authenticate(
            user=self.comite
        )

        response = self.client.get(
            reverse(
                "solicitud-detail",
                args=[solicitud.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class DocumentoAPITests(APITestCase):

    def setUp(self):
        self.media_temp = tempfile.TemporaryDirectory()

        self.override_media = override_settings(
            MEDIA_ROOT=self.media_temp.name
        )

        self.override_media.enable()

        self.addCleanup(
            self.override_media.disable
        )

        self.addCleanup(
            self.media_temp.cleanup
        )

        self.estudiante = Usuario.objects.create_user(
            username="documentos1",
            email="documentos1@test.com",
            password="Prueba12345",
            dpi="1234567890301",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.otro_estudiante = Usuario.objects.create_user(
            username="documentos2",
            email="documentos2@test.com",
            password="Prueba12345",
            dpi="1234567890302",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.convocatoria = Convocatoria.objects.create(
            nombre="Convocatoria documentos",
            tipo_beca="UNIVERSITARIO",
            descripcion="Pruebas de documentos",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        self.otra_solicitud = Solicitud.objects.create(
            estudiante=self.otro_estudiante,
            convocatoria=self.convocatoria,
        )

    def crear_archivo_pdf(
        self,
        nombre="documento.pdf",
    ):
        return SimpleUploadedFile(
            nombre,
            b"%PDF-1.4 archivo de prueba",
            content_type="application/pdf",
        )

    def test_estudiante_puede_subir_documento(self):
        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("documento-list"),
            {
                "solicitud": self.solicitud.id,
                "tipo": Documento.TIPO_DPI,
                "archivo": self.crear_archivo_pdf(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Documento.objects.count(),
            1,
        )

    def test_estudiante_no_puede_subir_a_otra_solicitud(self):
        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("documento-list"),
            {
                "solicitud": self.otra_solicitud.id,
                "tipo": Documento.TIPO_DPI,
                "archivo": self.crear_archivo_pdf(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Documento.objects.count(),
            0,
        )

    def test_no_permite_documento_principal_duplicado(self):
        Documento.objects.create(
            solicitud=self.solicitud,
            tipo=Documento.TIPO_DPI,
            archivo=self.crear_archivo_pdf(
                "dpi1.pdf"
            ),
        )

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("documento-list"),
            {
                "solicitud": self.solicitud.id,
                "tipo": Documento.TIPO_DPI,
                "archivo": self.crear_archivo_pdf(
                    "dpi2.pdf"
                ),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Documento.objects.count(),
            1,
        )

    def test_no_permite_formato_no_autorizado(self):
        archivo = SimpleUploadedFile(
            "archivo.exe",
            b"contenido de prueba",
            content_type="application/octet-stream",
        )

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("documento-list"),
            {
                "solicitud": self.solicitud.id,
                "tipo": Documento.TIPO_OTRO,
                "archivo": archivo,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_no_puede_subir_documento_en_evaluacion(self):
        self.solicitud.iniciar_evaluacion()

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("documento-list"),
            {
                "solicitud": self.solicitud.id,
                "tipo": Documento.TIPO_NOTAS,
                "archivo": self.crear_archivo_pdf(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_no_puede_eliminar_documento_en_evaluacion(self):
        documento = Documento.objects.create(
            solicitud=self.solicitud,
            tipo=Documento.TIPO_DPI,
            archivo=self.crear_archivo_pdf(),
        )

        self.solicitud.iniciar_evaluacion()

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.delete(
            reverse(
                "documento-detail",
                args=[documento.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertTrue(
            Documento.objects.filter(
                pk=documento.id
            ).exists()
        )


class ReglasNegocioSolicitudTests(APITestCase):

    def setUp(self):
        self.estudiante1 = Usuario.objects.create_user(
            username="reglas_estudiante1",
            email="reglas1@test.com",
            password="Prueba12345",
            dpi="1234567890501",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.estudiante2 = Usuario.objects.create_user(
            username="reglas_estudiante2",
            email="reglas2@test.com",
            password="Prueba12345",
            dpi="1234567890502",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.evaluador = Usuario.objects.create_user(
            username="reglas_comite",
            email="reglas_comite@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.COMITE,
        )

        self.convocatoria = Convocatoria.objects.create(
            nombre="Convocatoria reglas",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            descripcion="Pruebas finales",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=1,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.comite = Comite.objects.create(
            nombre="Comité reglas",
            convocatoria=self.convocatoria,
        )

        self.comite.integrantes.add(
            self.evaluador
        )

    def test_no_permite_solicitud_en_convocatoria_vencida(self):
        convocatoria_vencida = Convocatoria.objects.create(
            nombre="Convocatoria vencida",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            fecha_inicio=date.today() - timedelta(days=30),
            fecha_fin=date.today() - timedelta(days=1),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.client.force_authenticate(
            user=self.estudiante1
        )

        response = self.client.post(
            reverse("solicitud-list"),
            {
                "convocatoria": convocatoria_vencida.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Solicitud.objects.count(),
            0,
        )

    def test_no_permite_solicitud_en_convocatoria_futura(self):
        convocatoria_futura = Convocatoria.objects.create(
            nombre="Convocatoria futura",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            fecha_inicio=date.today() + timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.client.force_authenticate(
            user=self.estudiante1
        )

        response = self.client.post(
            reverse("solicitud-list"),
            {
                "convocatoria": convocatoria_futura.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Solicitud.objects.count(),
            0,
        )

    def test_no_permite_solicitud_duplicada(self):
        self.client.force_authenticate(
            user=self.estudiante1
        )

        url = reverse("solicitud-list")

        primera = self.client.post(
            url,
            {
                "convocatoria": self.convocatoria.id,
            },
            format="json",
        )

        segunda = self.client.post(
            url,
            {
                "convocatoria": self.convocatoria.id,
            },
            format="json",
        )

        self.assertEqual(
            primera.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            segunda.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Solicitud.objects.count(),
            1,
        )

    def test_no_permite_aprobar_mas_del_cupo(self):
        solicitud1 = Solicitud.objects.create(
            estudiante=self.estudiante1,
            convocatoria=self.convocatoria,
        )

        solicitud2 = Solicitud.objects.create(
            estudiante=self.estudiante2,
            convocatoria=self.convocatoria,
        )

        self.client.force_authenticate(
            user=self.evaluador
        )

        self.client.post(
            reverse(
                "solicitud-iniciar-evaluacion",
                args=[solicitud1.id],
            )
        )

        self.client.post(
            reverse(
                "solicitud-iniciar-evaluacion",
                args=[solicitud2.id],
            )
        )

        primera_aprobacion = self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud1.id],
            )
        )

        segunda_aprobacion = self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud2.id],
            )
        )

        self.assertEqual(
            primera_aprobacion.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            segunda_aprobacion.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        solicitud2.refresh_from_db()

        self.assertEqual(
            solicitud2.estado,
            Solicitud.EN_EVALUACION,
        )

        self.assertEqual(
            Solicitud.objects.filter(
                convocatoria=self.convocatoria,
                estado=Solicitud.APROBADA,
            ).count(),
            1,
        )

    def test_historial_registra_cambios_de_estado(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante1,
            convocatoria=self.convocatoria,
        )

        self.client.force_authenticate(
            user=self.evaluador
        )

        self.client.post(
            reverse(
                "solicitud-iniciar-evaluacion",
                args=[solicitud.id],
            )
        )

        self.client.post(
            reverse(
                "solicitud-rechazar",
                args=[solicitud.id],
            ),
            {
                "motivo": "No cumple con los requisitos."
            },
            format="json",
        )

        solicitud.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            Solicitud.RECHAZADA,
        )

        self.assertEqual(
            solicitud.motivo_rechazo,
            "No cumple con los requisitos.",
        )

        self.assertEqual(
            solicitud.historial.count(),
            2,
        )

        self.assertTrue(
            solicitud.historial.filter(
                estado_anterior=Solicitud.PENDIENTE,
                estado_nuevo=Solicitud.EN_EVALUACION,
            ).exists()
        )

        self.assertTrue(
            solicitud.historial.filter(
                estado_anterior=Solicitud.EN_EVALUACION,
                estado_nuevo=Solicitud.RECHAZADA,
            ).exists()
        )

    def test_estado_final_no_permite_nueva_transicion(self):
        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante1,
            convocatoria=self.convocatoria,
        )

        self.client.force_authenticate(
            user=self.evaluador
        )

        self.client.post(
            reverse(
                "solicitud-iniciar-evaluacion",
                args=[solicitud.id],
            )
        )

        self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud.id],
            )
        )

        response = self.client.post(
            reverse(
                "solicitud-rechazar",
                args=[solicitud.id],
            ),
            {
                "motivo": "Intento inválido"
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        solicitud.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            Solicitud.APROBADA,
        )