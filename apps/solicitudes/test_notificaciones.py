from datetime import date, timedelta

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.convocatorias.models import Convocatoria
from apps.evaluaciones.models import Comite
from apps.usuarios.models import Usuario

from .models import HistorialEstado, Notificacion, Solicitud


class NotificacionTests(APITestCase):

    def setUp(self):
        self.estudiante = Usuario.objects.create_user(
            username="estudiante_notificaciones",
            email="estudiante.notificaciones@test.com",
            password="Prueba12345",
            dpi="1234567890801",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=(
                Usuario.NivelAcademico.UNIVERSITARIO
            ),
        )

        self.otro_estudiante = Usuario.objects.create_user(
            username="otro_estudiante_notificaciones",
            email="otro.notificaciones@test.com",
            password="Prueba12345",
            dpi="1234567890802",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=(
                Usuario.NivelAcademico.UNIVERSITARIO
            ),
        )

        self.aprobador1 = Usuario.objects.create_user(
            username="notificaciones_aprobador1",
            email="notificaciones.aprobador1@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.COMITE,
        )

        self.aprobador2 = Usuario.objects.create_user(
            username="notificaciones_aprobador2",
            email="notificaciones.aprobador2@test.com",
            password="Prueba12345",
            rol=Usuario.Rol.COMITE,
        )

        self.convocatoria = Convocatoria.objects.create(
            nombre="Convocatoria notificaciones",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            descripcion=(
                "Convocatoria para probar notificaciones."
            ),
            fecha_inicio=date.today(),
            fecha_fin=(
                date.today()
                + timedelta(days=30)
            ),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        self.comite = Comite.objects.create(
            nombre="Comité notificaciones",
            convocatoria=self.convocatoria,
        )

        self.comite.integrantes.add(
            self.aprobador1,
            self.aprobador2,
        )

    def crear_solicitud(
        self,
        monto="8000.00",
    ):
        return Solicitud.objects.create(
            estudiante=self.estudiante,
            convocatoria=self.convocatoria,
            motivo="Solicitud de prueba.",
            monto_solicitado=monto,
        )

    def iniciar_evaluacion(
        self,
        solicitud,
    ):
        self.client.force_authenticate(
            user=self.aprobador1
        )

        return self.client.post(
            reverse(
                "solicitud-iniciar-evaluacion",
                args=[solicitud.id],
            )
        )

    def test_cambio_estado_registra_evento_y_notificacion(
        self,
    ):
        solicitud = self.crear_solicitud()

        response = self.iniciar_evaluacion(
            solicitud
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

        self.assertTrue(
            HistorialEstado.objects.filter(
                solicitud=solicitud,
                estado_anterior=Solicitud.PENDIENTE,
                estado_nuevo=Solicitud.EN_EVALUACION,
            ).exists()
        )

        notificacion = Notificacion.objects.get(
            solicitud=solicitud,
            destinatario=self.estudiante,
        )

        self.assertIn(
            "evaluación",
            notificacion.mensaje.lower(),
        )

        self.assertFalse(
            notificacion.leida
        )

    def test_estudiante_solo_puede_ver_sus_notificaciones(
        self,
    ):
        solicitud = self.crear_solicitud()

        self.iniciar_evaluacion(
            solicitud
        )

        otra_convocatoria = Convocatoria.objects.create(
            nombre="Otra convocatoria",
            tipo_beca=Convocatoria.TIPO_UNIVERSITARIO,
            descripcion="Segunda convocatoria.",
            fecha_inicio=date.today(),
            fecha_fin=(
                date.today()
                + timedelta(days=30)
            ),
            cupo=10,
            estado=Convocatoria.ESTADO_ACTIVA,
        )

        otra_solicitud = Solicitud.objects.create(
            estudiante=self.otro_estudiante,
            convocatoria=otra_convocatoria,
            motivo="Otra solicitud.",
            monto_solicitado="5000.00",
        )

        Notificacion.objects.create(
            destinatario=self.otro_estudiante,
            solicitud=otra_solicitud,
            mensaje="Notificación de otro estudiante.",
        )

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.get(
            reverse(
                "notificacion-list"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        if isinstance(
            response.data,
            dict,
        ):
            datos = response.data.get(
                "results",
                [],
            )
        else:
            datos = response.data

        self.assertEqual(
            len(datos),
            1,
        )

        self.assertEqual(
            datos[0]["solicitud"],
            solicitud.id,
        )

    def test_estudiante_puede_marcar_notificacion_como_leida(
        self,
    ):
        solicitud = self.crear_solicitud()

        self.iniciar_evaluacion(
            solicitud
        )

        notificacion = Notificacion.objects.get(
            solicitud=solicitud,
            destinatario=self.estudiante,
        )

        self.assertFalse(
            notificacion.leida
        )

        self.client.force_authenticate(
            user=self.estudiante
        )

        response = self.client.post(
            reverse(
                "notificacion-marcar-leida",
                args=[notificacion.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notificacion.refresh_from_db()

        self.assertTrue(
            notificacion.leida
        )

    def test_otro_estudiante_no_puede_marcar_notificacion_como_leida(
        self,
    ):
        solicitud = self.crear_solicitud()

        self.iniciar_evaluacion(
            solicitud
        )

        notificacion = Notificacion.objects.get(
            solicitud=solicitud,
            destinatario=self.estudiante,
        )

        self.client.force_authenticate(
            user=self.otro_estudiante
        )

        response = self.client.post(
            reverse(
                "notificacion-marcar-leida",
                args=[notificacion.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        notificacion.refresh_from_db()

        self.assertFalse(
            notificacion.leida
        )

    def test_doble_aprobacion_genera_notificaciones(
        self,
    ):
        solicitud = self.crear_solicitud(
            monto="15000.00"
        )

        inicio = self.iniciar_evaluacion(
            solicitud
        )

        self.assertEqual(
            inicio.status_code,
            status.HTTP_200_OK,
        )

        primera = self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud.id],
            )
        )

        self.assertEqual(
            primera.status_code,
            status.HTTP_200_OK,
        )

        solicitud.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            Solicitud.PENDIENTE_SEGUNDA_APROBACION,
        )

        self.assertTrue(
            Notificacion.objects.filter(
                solicitud=solicitud,
                destinatario=self.estudiante,
                mensaje__icontains="primera aprobación",
            ).exists()
        )

        self.client.force_authenticate(
            user=self.aprobador2
        )

        segunda = self.client.post(
            reverse(
                "solicitud-aprobar",
                args=[solicitud.id],
            )
        )

        self.assertEqual(
            segunda.status_code,
            status.HTTP_200_OK,
        )

        solicitud.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            Solicitud.APROBADA,
        )

        self.assertTrue(
            Notificacion.objects.filter(
                solicitud=solicitud,
                destinatario=self.estudiante,
                mensaje__icontains="aprobada",
            ).exists()
        )

        self.assertEqual(
            Notificacion.objects.filter(
                solicitud=solicitud,
                destinatario=self.estudiante,
            ).count(),
            3,
        )