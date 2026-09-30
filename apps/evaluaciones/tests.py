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

        # La solicitud debe estar en evaluación
        # antes de poder recibir evaluaciones.
        self.solicitud.iniciar_evaluacion()

        self.comite = Comite.objects.create(
            nombre="Comité Universitario",
            convocatoria=self.convocatoria,
        )

        self.comite.integrantes.add(
            self.evaluador
        )

    def test_miembro_comite_puede_evaluar(self):
        """
        Un miembro del comité asignado puede
        registrar una evaluación.
        """

        self.client.force_authenticate(
            user=self.evaluador
        )

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

        self.assertEqual(
            float(evaluacion.puntaje),
            85.0,
        )

    def test_no_puede_usar_otro_evaluador(self):
        """
        Aunque se envíe el ID de otro evaluador,
        Django utiliza al usuario autenticado.
        """

        self.client.force_authenticate(
            user=self.evaluador
        )

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
        """
        Un miembro del comité que no pertenece
        al comité de la convocatoria no puede evaluar.
        """

        self.client.force_authenticate(
            user=self.otro_evaluador
        )

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
        """
        El mismo evaluador no puede evaluar
        dos veces la misma solicitud.
        """

        Evaluacion.objects.create(
            solicitud=self.solicitud,
            evaluador=self.evaluador,
            puntaje=80,
            comentario="Primera evaluación",
        )

        self.client.force_authenticate(
            user=self.evaluador
        )

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 90,
                "comentario": "Segunda evaluación",
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
        """
        Un estudiante no tiene permiso
        para registrar evaluaciones.
        """

        self.client.force_authenticate(
            user=self.estudiante
        )

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
        """
        Comprueba Factory + Strategy para
        una beca universitaria.
        """

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

        self.client.force_authenticate(
            user=self.evaluador
        )

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

        self.assertEqual(
            response.data["cantidad_evaluaciones"],
            2,
        )

    def test_no_puede_evaluar_solicitud_pendiente(self):
        """
        Una solicitud PENDIENTE todavía
        no puede recibir evaluaciones.
        """

        self.solicitud.estado = Solicitud.PENDIENTE
        self.solicitud.save(
            update_fields=["estado"]
        )

        self.client.force_authenticate(
            user=self.evaluador
        )

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 80,
                "comentario": "Prueba.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Evaluacion.objects.count(),
            0,
        )

    def test_no_permite_puntaje_mayor_a_100(self):
        """
        El puntaje máximo permitido es 100.
        """

        self.client.force_authenticate(
            user=self.evaluador
        )

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": 150,
                "comentario": "Puntaje inválido.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Evaluacion.objects.count(),
            0,
        )

    def test_no_permite_puntaje_negativo(self):
        """
        El puntaje mínimo permitido es 0.
        """

        self.client.force_authenticate(
            user=self.evaluador
        )

        response = self.client.post(
            reverse("evaluacion-list"),
            {
                "solicitud": self.solicitud.id,
                "puntaje": -10,
                "comentario": "Puntaje inválido.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Evaluacion.objects.count(),
            0,
        )