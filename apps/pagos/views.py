from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.usuarios.models import Usuario

from .forms import PagoForm
from .models import Pago
from .services import solicitudes_por_pagar


@login_required
def subir_pago(request):
    if request.user.rol != Usuario.Rol.ESTUDIANTE:
        messages.error(request, "Esta sección es exclusiva para estudiantes.")
        return redirect("inicio")

    pendientes = solicitudes_por_pagar(request.user)
    solicitud_id = request.POST.get("solicitud") or request.GET.get("solicitud")

    solicitud = None
    if not solicitud_id:
        solicitud = pendientes.first()
    elif str(solicitud_id).isdigit():
        solicitud = pendientes.filter(pk=solicitud_id).first()

    historial_pagos = Pago.objects.filter(
        estudiante=request.user
    ).select_related("solicitud__convocatoria")

    if solicitud is None:
        if not historial_pagos.exists():
            messages.error(request, "No tienes una beca aprobada pendiente de pago.")
            return redirect("inicio")
        return render(request, "pagos/subir_pago.html", {
            "form": None,
            "puede_pagar": False,
            "historial_pagos": historial_pagos,
        })

    condicion = solicitud.condicion_pago

    if request.method == "POST":
        form = PagoForm(request.POST, request.FILES)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.estudiante = request.user                     # nunca viene del formulario
            pago.solicitud = solicitud                         # tampoco
            pago.monto_pagado = condicion.monto_a_pagar        # lo fija el sistema
            pago.concepto = f"Inscripción - {solicitud.convocatoria.nombre}"
            pago.save()
            messages.success(request, "¡Tu comprobante de pago ha sido enviado y está en revisión!")
            return redirect("subir_pago")
    else:
        form = PagoForm()

    return render(request, "pagos/subir_pago.html", {
        "form": form,
        "puede_pagar": True,
        "solicitud": solicitud,
        "condicion": condicion,
        "historial_pagos": historial_pagos,
    })