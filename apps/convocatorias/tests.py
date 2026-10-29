from datetime import date, timedelta

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.usuarios.models import Usuario

from .models import Convocatoria


class ConvocatoriaAPITests(APITestCase):

    def setUp(self):
        self.estudiante = Usuario.objects.create_user(
            username="estudiante_convocatoria",
            email="estudiante_convocatoria@test.com",
            password="Prueba12345",
            dpi="1234567890401",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.administrador = Usuario.objects.create_user(
            username="administrador1",
            email="administrador@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.ADMINISTRADOR,
        )

        self.convocatoria_activa = Convocatoria.objects.create(
            nombre="Beca activa",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            descripcion="Convocatoria activa de prueba",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.convocatoria_cerrada = Convocatoria.objects.create(
            nombre="Beca cerrada",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            descripcion="Convocatoria cerrada",
            fecha_inicio=date.today() - timedelta(days=60),
            fecha_fin=date.today() - timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_CERRADA,
        )

    def test_usuario_autenticado_puede_ver_convocatorias(self):
        """
        Un estudiante autenticado puede consultar
        las convocatorias.
        """

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.get(
            reverse("convocatoria-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_filtro_solo_muestra_convocatorias_activas(self):
        """
        ?activas=true debe retornar únicamente
        convocatorias con estado ACTIVA.
        """

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.get(
            reverse("convocatoria-list"),
            {
                "activas": "true"
            },
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
            self.convocatoria_activa.id,
        )

    def test_estudiante_no_puede_crear_convocatoria(self):
        """
        Solo un administrador puede crear convocatorias.
        """

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse("convocatoria-list"),
            {
                "nombre": "Beca nueva",
                "tipo_beca": Convocatoria.TIPO_UNIVERSITARIO,
                "descripcion": "Prueba",
                "fecha_inicio": date.today(),
                "fecha_fin": date.today() + timedelta(days=30),
                "cupo": 20,
                "estado": Convocatoria.ESTADO_ACTIVA,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_administrador_puede_crear_convocatoria(self):
        """
        El administrador puede crear convocatorias.
        """

        self.client.force_authenticate(
            user=self.administrador
        )

        response = self.client.post(
            reverse("convocatoria-list"),
            {
                "nombre": "Beca Posgrado 2026",
                "tipo_beca": Convocatoria.TIPO_POSGRADO,
                "descripcion": "Beca para posgrado",
                "fecha_inicio": date.today(),
                "fecha_fin": date.today() + timedelta(days=60),
                "cupo": 15,
                "estado": Convocatoria.ESTADO_ACTIVA,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Convocatoria.objects.filter(
                nombre="Beca Posgrado 2026"
            ).exists()
        )

    def test_no_permite_fecha_fin_anterior_a_inicio(self):
        """
        La fecha final no puede ser anterior
        a la fecha inicial.
        """

        self.client.force_authenticate(
            user=self.administrador
        )

        response = self.client.post(
            reverse("convocatoria-list"),
            {
                "nombre": "Convocatoria inválida",
                "tipo_beca": Convocatoria.TIPO_MEDIO,
                "descripcion": "Fechas inválidas",
                "fecha_inicio": date.today() + timedelta(days=10),
                "fecha_fin": date.today(),
                "cupo": 10,
                "estado": Convocatoria.ESTADO_ACTIVA,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_no_permite_cupo_cero(self):
        """
        El cupo debe ser mayor a cero.
        """

        self.client.force_authenticate(
            user=self.administrador
        )

        response = self.client.post(
            reverse("convocatoria-list"),
            {
                "nombre": "Convocatoria sin cupo",
                "tipo_beca": Convocatoria.TIPO_MEDIO,
                "descripcion": "Cupo inválido",
                "fecha_inicio": date.today(),
                "fecha_fin": date.today() + timedelta(days=30),
                "cupo": 0,
                "estado": Convocatoria.ESTADO_ACTIVA,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_convocatoria_activa_y_en_fecha_esta_abierta(self):
        """
        Estado ACTIVA + fechas válidas = convocatoria abierta.
        """

        self.assertTrue(
            self.convocatoria_activa.esta_abierta()
        )

    def test_convocatoria_vencida_no_esta_abierta(self):
        """
        Aunque una convocatoria tenga estado ACTIVA,
        si ya venció no debe considerarse abierta.
        """

        convocatoria = Convocatoria.objects.create(
            nombre="Convocatoria vencida",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            fecha_inicio=date.today() - timedelta(days=60),
            fecha_fin=date.today() - timedelta(days=1),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.assertFalse(
            convocatoria.esta_abierta()
        )

    def test_convocatoria_futura_no_esta_abierta(self):
        """
        Una convocatoria que todavía no inicia
        no debe aceptar solicitudes.
        """

        convocatoria = Convocatoria.objects.create(
            nombre="Convocatoria futura",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            fecha_inicio=date.today() + timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=30),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.assertFalse(
            convocatoria.esta_abierta()
        )