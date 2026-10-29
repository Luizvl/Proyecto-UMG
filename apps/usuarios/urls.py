from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "usuarios"

urlpatterns = [
    path("registro/", views.registro_estudiante, name="registro"),
    path("login/", views.LoginUsuarioView.as_view(), name="login"),
    path("logout/", views.LogoutUsuarioView.as_view(), name="logout"),
    path("panel/", views.panel, name="panel"),

    # ---------- Recuperación de contraseña (vistas que ya trae Django) ----------
    # 1. El usuario escribe su correo
    path(
        "recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/recuperar_form.html",
            email_template_name="usuarios/recuperar_email.txt",
            subject_template_name="usuarios/recuperar_asunto.txt",
            success_url=reverse_lazy("usuarios:recuperar_enviado"),
        ),
        name="recuperar",
    ),
    # 2. Aviso de "te enviamos un correo"
    path(
        "recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/recuperar_enviado.html",
        ),
        name="recuperar_enviado",
    ),
    # 3. Enlace del correo: escribe la nueva contraseña
    path(
        "recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/recuperar_confirmar.html",
            success_url=reverse_lazy("usuarios:recuperar_listo"),
        ),
        name="recuperar_confirmar",
    ),
    # 4. Confirmación final
    path(
        "recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/recuperar_listo.html",
        ),
        name="recuperar_listo",
    ),
]
