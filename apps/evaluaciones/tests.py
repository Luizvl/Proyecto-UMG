from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.convocatorias.models import Convocatoria
from apps.solicitudes.models import Solicitud
from apps.usuarios.models import Usuario

from .models import Comite, Evaluacion


class EvaluacionAPITests(APITestCase):

    def setUp(self):
        self.estudiante = Usuario.objects.create_user(
            username="estudiante1",
            email="estudiante1@test.com",
            password="Prueba12345",
            dpi="1234567890201",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.evaluador = Usuario.objects.create_user(
            username="evaluador1",
            email="evaluador1@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.COMITE,
        )

        self.otro_evaluador = Usuario.objects.create_user(
            username="evaluador2",
            email="evaluador2@test.com",
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

        self.solicitud = Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
        )

        self.comite = Comite.objects.create(
            nombre="Comité Universitario",
            convocatoria=self.convocatoria,
        )

        self.comite.integrantes.add(self.evaluador)

    def test_miembro_comite_puede_evaluar(self):
        self.client.force_authenticate(user=self.evaluador)

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 85,
                "comentario": "Cumple los requisitos.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        evaluacion = Evaluacion.objects.get()

        self.assertEqual(
            evaluacion.evaluador,
            self.evaluador,
        )

    def test_no_puede_usar_otro_evaluador(self):
        self.client.force_authenticate(user=self.evaluador)

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "evaluador": self.otro_evaluador.id,
                "puntaje": 90,
                "comentario": "Evaluación.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        evaluacion = Evaluacion.objects.get()

        self.assertEqual(
            evaluacion.evaluador,
            self.evaluador,
        )

        self.assertNotEqual(
            evaluacion.evaluador,
            self.otro_evaluador,
        )

    def test_usuario_no_asignado_no_puede_evaluar(self):
        self.client.force_authenticate(user=self.otro_evaluador)

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 75,
                "comentario": "Prueba.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_no_permite_evaluacion_duplicada(self):
        Evaluacion.objects.create(
            solicitud=self.solicitud,
            evaluador=self.evaluador,
            puntaje=80,
        )

        self.client.force_authenticate(user=self.evaluador)

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 90,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Evaluacion.objects.count(),
            1,
        )

    def test_estudiante_no_puede_evaluar(self):
        self.client.force_authenticate(user=self.estudiante)

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 100,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_calcula_puntaje_final(self):
        Evaluacion.objects.create(
            solicitud=self.solicitud,
            evaluador=self.evaluador,
            puntaje=90,
        )

        Evaluacion.objects.create(
            solicitud=self.solicitud,
            evaluador=self.otro_evaluador,
            puntaje=70,
        )

        self.client.force_authenticate(user=self.evaluador)

        response = self.client.get(
            reverse(
                "evaluacion-puntaje-final",
                args=[self.solicitud.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "puntaje_final",
            response.data,
        )

        self.assertEqual(
            response.data["estrategia"],
            "PromedioPonderadoStrategy",
        )