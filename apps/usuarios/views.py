from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import RegistroEstudianteForm


def registro_estudiante(request):
    if request.method == "POST":
        form = RegistroEstudianteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Tu cuenta fue creada correctamente. Ya puedes iniciar sesión."
            )
            return redirect("usuarios:registro")
    else:
        form = RegistroEstudianteForm()

    return render(request, "usuarios/registro.html", {"form": form})
