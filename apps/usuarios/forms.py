from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class RegistroEstudianteForm(UserCreationForm):

    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    dpi = forms.CharField(label="DPI", max_length=13, min_length=13)
    email = forms.EmailField(label="Correo electrónico")

    nivel_academico = forms.ChoiceField(
        label="Nivel académico",
        choices=Usuario.NivelAcademico.choices,
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput,
        help_text=(
            "La contraseña debe contener al menos 8 caracteres, "
            "no puede ser demasiado similar a tus datos personales, "
            "no puede ser una contraseña de uso común "
            "y no puede contener únicamente números."
        ),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
        help_text="Ingresa nuevamente la misma contraseña para verificarla.",
    )

    class Meta:
        model = Usuario
        fields = (
            "first_name", "last_name", "dpi", "email",
            "nivel_academico", "password1", "password2",
        )

    def clean_dpi(self):
        dpi = self.cleaned_data["dpi"]
        if not dpi.isdigit():
            raise forms.ValidationError("El DPI debe contener únicamente números.")
        if Usuario.objects.filter(dpi=dpi).exists():
            raise forms.ValidationError("Este DPI ya se encuentra registrado.")
        return dpi

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya se encuentra registrado.")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = self.cleaned_data["email"]
        usuario.email = self.cleaned_data["email"]
        usuario.rol = Usuario.Rol.ESTUDIANTE
        if commit:
            usuario.save()
        return usuario
