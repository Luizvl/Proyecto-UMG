from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


# Mensajes amigables para los errores de contraseña que genera Django.
# La clave es el "código" del error; así no dependemos del texto original.
MENSAJES_CONTRASENA = {
    "password_too_short": "Usa al menos 8 caracteres.",
    "password_too_common": "Esa contraseña es muy común. Elige una más difícil de adivinar.",
    "password_entirely_numeric": "Agrega al menos una letra: no puede ser solo números.",
    "password_too_similar": "Se parece mucho a tu nombre o correo. Elige una diferente.",
    "password_mismatch": "Las contraseñas no coinciden. Escríbelas de nuevo.",
}


class RegistroEstudianteForm(UserCreationForm):

    first_name = forms.CharField(
        label="Nombres", max_length=150,
        error_messages={"required": "Escribe tus nombres."},
    )
    last_name = forms.CharField(
        label="Apellidos", max_length=150,
        error_messages={"required": "Escribe tus apellidos."},
    )
    # Se acepta con espacios (1234 56789 0101); clean_dpi los quita.
    dpi = forms.CharField(
        label="DPI", max_length=20,
        error_messages={"required": "Escribe tu número de DPI."},
    )
    email = forms.EmailField(
        label="Correo electrónico",
        error_messages={
            "required": "Escribe tu correo electrónico.",
            "invalid": "Ese correo no parece válido. Ejemplo: nombre@gmail.com",
        },
    )
    nivel_academico = forms.ChoiceField(
        label="Nivel académico",
        choices=Usuario.NivelAcademico.choices,
        error_messages={"required": "Elige tu nivel académico."},
    )
    password1 = forms.CharField(
        label="Contraseña", widget=forms.PasswordInput,
        error_messages={"required": "Crea una contraseña."},
    )
    password2 = forms.CharField(
        label="Confirmar contraseña", widget=forms.PasswordInput,
        error_messages={"required": "Escribe de nuevo tu contraseña."},
    )
    terminos = forms.BooleanField(
        label="Acepto términos y condiciones",
        error_messages={"required": "Debes aceptar los términos y condiciones para crear tu cuenta."},
    )

    class Meta:
        model = Usuario
        fields = (
            "first_name", "last_name", "dpi", "email",
            "nivel_academico", "password1", "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La plantilla usa estas banderas para mostrar enlaces de ayuda
        self.dpi_registrado = False
        self.email_registrado = False

    def errores_amigables(self):
        """
        Lista de errores lista para la ventana flotante: un título corto,
        el mensaje y, si aplica, un enlace de ayuda. Va en el orden del formulario.
        """
        titulos = {
            "first_name": "Faltan tus nombres",
            "last_name": "Faltan tus apellidos",
            "dpi": "Revisa tu DPI",
            "email": "Revisa tu correo",
            "nivel_academico": "Elige tu nivel académico",
            "password1": "Revisa tu contraseña",
            "password2": "Revisa tu contraseña",
            "terminos": "Falta aceptar los términos",
        }
        lista = []
        for nombre in ["first_name", "last_name", "dpi", "email", "nivel_academico", "password1", "password2", "terminos"]:
            if nombre not in self.errors:
                continue
            item = {
                "campo": self[nombre].id_for_label,
                "titulo": titulos[nombre],
                "texto": " ".join(self.errors[nombre]),
                "ayuda": None,
            }
            if nombre == "dpi" and self.dpi_registrado:
                item.update(titulo="Este DPI ya está registrado",
                            texto="Parece que ya existe una cuenta con este número de DPI.",
                            ayuda="login")
            if nombre == "email" and self.email_registrado:
                item.update(titulo="Este correo ya tiene una cuenta",
                            texto="Parece que ya te registraste con este correo.",
                            ayuda="login")
            # La contraseña se muestra una sola vez aunque falle en los dos campos
            if nombre == "password2" and any(i["titulo"] == "Revisa tu contraseña" for i in lista):
                lista[-1]["texto"] += " " + item["texto"]
                continue
            lista.append(item)
        return lista

    def clean_dpi(self):
        dpi = self.cleaned_data["dpi"].replace(" ", "").replace("-", "")
        if not dpi.isdigit():
            raise forms.ValidationError("El DPI solo lleva números.")
        if len(dpi) != 13:
            raise forms.ValidationError(
                f"El DPI tiene 13 números y escribiste {len(dpi)}. Revisa que no falte ni sobre ninguno."
            )
        if Usuario.objects.filter(dpi=dpi).exists():
            self.dpi_registrado = True
            raise forms.ValidationError("Ya existe una cuenta con este DPI.")
        return dpi

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email=email).exists():
            self.email_registrado = True
            raise forms.ValidationError("Este correo ya tiene una cuenta.")
        return email

    def _post_clean(self):
        """
        Django valida la contraseña aquí y genera sus propios mensajes.
        Los cambiamos por versiones más claras usando el código de cada error.
        """
        super()._post_clean()
        for campo in ("password1", "password2"):
            if campo in self._errors:
                amigables = []
                for error in self._errors[campo].as_data():
                    texto = MENSAJES_CONTRASENA.get(error.code, " ".join(error.messages))
                    if texto not in amigables:
                        amigables.append(texto)
                self._errors[campo] = self.error_class(amigables)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = self.cleaned_data["email"]
        usuario.email = self.cleaned_data["email"]
        usuario.rol = Usuario.Rol.ESTUDIANTE
        if commit:
            usuario.save()
        return usuario
