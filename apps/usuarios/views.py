from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import RegistroEstudianteForm
from .models import Usuario


def registro_estudiante(request):
    if request.method == "POST":
        form = RegistroEstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Tu cuenta fue creada correctamente. Ya puedes iniciar sesión."
            )
            return redirect("usuarios:login")
    else:
        form = RegistroEstudianteForm()

    return render(request, "usuarios/registro.html", {"form": form})


class LoginUsuarioView(LoginView):
    """
    Login basado en la vista de Django, solo con plantilla propia y
    redirección distinta según el rol del usuario.
    """
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("usuarios:panel")


class LogoutUsuarioView(LogoutView):
    next_page = reverse_lazy("usuarios:login")


@login_required(login_url="usuarios:login")
def panel(request):
    """
    Punto de entrada único después de iniciar sesión. Por ahora es un
    placeholder que confirma el rol; cuando existan las pantallas reales
    de cada rol (convocatorias, solicitudes, evaluación), este método
    se encarga de redirigir a cada una según corresponda.
    """
    usuario = request.user
    contexto = {
        "usuario": usuario,
        "es_estudiante": usuario.rol == Usuario.Rol.ESTUDIANTE,
        "es_comite": usuario.rol == Usuario.Rol.COMITE,
        "es_administrador": usuario.rol == Usuario.Rol.ADMINISTRADOR,
    }
    return render(request, "usuarios/panel.html", contexto)

