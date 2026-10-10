from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class UsuarioAutenticacionTests(TestCase):

    def setUp(self):
        self.password = "ClaveSegura2026!"

        self.estudiante = Usuario.objects.create_user(
            username="usuario_existente",
            email="existente@test.com",
            password=self.password,
            dpi="1234567890601",
            first_name="Usuario",
            last_name="Existente",
            rol=Usuario.Rol.ESTUDIANTE,
            nivel_academico=Usuario.NivelAcademico.UNIVERSITARIO,
        )

    def datos_registro(self):
        return {
            "first_name": "Jonathan",
            "last_name": "Prueba",
            "dpi": "1234567890602",
            "email": "jonathan.prueba@test.com",
            "nivel_academico": Usuario.NivelAcademico.UNIVERSITARIO,
            "password1": "NuevaClave2026!",
            "password2": "NuevaClave2026!",
        }

    def test_registro_estudiante_crea_usuario_correctamente(self):
        """
        El formulario público debe crear únicamente
        usuarios con rol ESTUDIANTE.
        """

        response = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        usuario = Usuario.objects.get(
            email="jonathan.prueba@test.com"
        )

        self.assertEqual(
            usuario.rol,
            Usuario.Rol.ESTUDIANTE,
        )

        self.assertEqual(
            usuario.username,
            "jonathan.prueba@test.com",
        )

        self.assertEqual(
            usuario.nivel_academico,
            Usuario.NivelAcademico.UNIVERSITARIO,
        )

        self.assertTrue(
            usuario.check_password(
                "NuevaClave2026!"
            )
        )

    def test_no_permite_correo_duplicado(self):
        """
        Dos usuarios no pueden registrarse
        con el mismo correo electrónico.
        """

        datos = self.datos_registro()

        datos["email"] = self.estudiante.email

        response = self.client.post(
            reverse("usuarios:registro"),
            datos,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Usuario.objects.filter(
                email=self.estudiante.email
            ).count(),
            1,
        )

    def test_no_permite_dpi_duplicado(self):
        """
        Dos estudiantes no pueden utilizar
        el mismo DPI.
        """

        datos = self.datos_registro()

        datos["dpi"] = self.estudiante.dpi

        response = self.client.post(
            reverse("usuarios:registro"),
            datos,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Usuario.objects.filter(
                dpi=self.estudiante.dpi
            ).count(),
            1,
        )

    def test_login_correcto(self):
        """
        Un usuario registrado puede iniciar sesión
        utilizando su correo electrónico.
        """

        response = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.estudiante.email,
                "password": self.password,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_login_con_password_incorrecto(self):
        """
        Una contraseña incorrecta no debe
        autenticar al usuario.
        """

        response = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.estudiante.email,
                "password": "PasswordIncorrecto123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_panel_requiere_autenticacion(self):
        """
        Un usuario anónimo no puede ingresar
        directamente al panel.
        """

        response = self.client.get(
            reverse("usuarios:panel")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            "/usuarios/login/",
            response.url,
        )

    def test_panel_identifica_rol_estudiante(self):
        """
        El panel debe reconocer correctamente
        el rol del usuario autenticado.
        """

        self.client.force_login(
            self.estudiante
        )

        response = self.client.get(
            reverse("usuarios:panel")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.context["es_estudiante"]
        )

        self.assertFalse(
            response.context["es_comite"]
        )

        self.assertFalse(
            response.context["es_administrador"]
        )

    def test_logout_cierra_sesion(self):
        """
        El logout debe eliminar la sesión
        autenticada del usuario.
        """

        self.client.force_login(
            self.estudiante
        )

        self.assertIn(
            "_auth_user_id",
            self.client.session,
        )

        response = self.client.post(
            reverse("usuarios:logout")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )