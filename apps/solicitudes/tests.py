from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.convocatorias.models import Convocatoria
from apps.usuarios.models import Usuario

from .models import Solicitud


class SolicitudAPITests(APITestCase):

    def setUp(self):
        # Estudiante principal
        self.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            email="estudiante1@test.com",
            password="Prueba12345",
            dpi="1234567890101",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        # Segundo estudiante
        self.otro_estudiante = Usuario.objects.create_user(
            username="estudiante2",
            email="estudiante2@test.com",
            password="Prueba12345",
            dpi="1234567890102",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        # Usuario miembro del comité
        self.comite = Usuario.objects.create_user(
            username="comite1",
            email="comite@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.COMITE,
        )

        # Convocatoria activa
        self.convocatoria = Convocatoria.objects.create(
            nombre="Beca Universitaria 2026",
            tipo_beca="UNIVERSITARIO",
            descripcion="Convocatoria de prueba",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

    def test_estudiante_crea_solicitud_a_su_nombre(self):
        """
        Aunque el estudiante intente enviar el ID de otra persona,
        la solicitud debe quedar vinculada al usuario autenticado.
        """

        self.client.force_authenticate(user=self.estudiante)

        url = reverse("solicitud-list")

        data = {
            "estudiante": self.otro_estudiante.id,
            "convocatoria": self.convocatoria.id,
        }

        response = self.client.post(
            url,
            data,
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
        """
        Un estudiante no debe poder consultar solicitudes
        pertenecientes a otros estudiantes.
        """

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
        """
        Un miembro del comité puede pasar:
        PENDIENTE -> EN_EVALUACION -> APROBADA.
        """

        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        self.client.force_authenticate(
            user=self.comite
        )

        url_iniciar = reverse(
            "solicitud-iniciar-evaluacion",
            args=[solicitud.id],
        )

        response = self.client.post(
            url_iniciar,
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

        url_aprobar = reverse(
            "solicitud-aprobar",
            args=[solicitud.id],
        )

        response = self.client.post(
            url_aprobar,
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
        """
        Un estudiante no tiene permiso para aprobar solicitudes.
        """

        solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        solicitud.iniciar_evaluacion()

        self.client.force_authenticate(
            user=self.estudiante
        )

        url = reverse(
            "solicitud-aprobar",
            args=[solicitud.id],
        )

        response = self.client.post(
            url,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )