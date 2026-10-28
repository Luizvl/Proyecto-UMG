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
    Punto de entrada único después de iniciar sesión.

    - Estudiante: panel con el estado real de su solicitud, sus documentos,
      las convocatorias abiertas y su actividad reciente.
    - Comité / Administrador: tarjeta simple con acceso al panel administrativo.
    """
    usuario = request.user
    contexto = {
        "usuario": usuario,
        "es_estudiante": usuario.rol == Usuario.Rol.ESTUDIANTE,
        "es_comite": usuario.rol == Usuario.Rol.COMITE,
        "es_administrador": usuario.rol == Usuario.Rol.ADMINISTRADOR,
    }
    if contexto["es_estudiante"]:
        contexto.update(_datos_panel_estudiante(usuario))
        return render(request, "usuarios/panel_estudiante.html", contexto)
    return render(request, "usuarios/panel.html", contexto)


# Documentos que toda solicitud debe tener para considerarse completa
DOCUMENTOS_OBLIGATORIOS = ["DPI", "CONSTANCIA_ESTUDIOS", "NOTAS"]


def _datos_panel_estudiante(usuario):
    """Reúne la información que muestra el panel del estudiante."""
    # Import local para no crear dependencias circulares entre apps
    from apps.convocatorias.models import Convocatoria
    from apps.solicitudes.models import Documento, HistorialEstado, Solicitud

    solicitud = (
        Solicitud.objects.filter(estudiante=usuario)
        .select_related("convocatoria")
        .first()  # el modelo ordena por fecha de creación descendente
    )

    # ---- Convocatorias abiertas hoy ----
    convocatorias_abiertas = sum(
        1 for c in Convocatoria.objects.filter(estado=Convocatoria.ESTADO_ACTIVA)
        if c.esta_abierta()
    )

    # ---- Documentos ----
    documentos = Documento.objects.filter(solicitud=solicitud) if solicitud else Documento.objects.none()
    tipos_subidos = set(documentos.values_list("tipo", flat=True))
    docs_completos = len([t for t in DOCUMENTOS_OBLIGATORIOS if t in tipos_subidos])
    docs_total = len(DOCUMENTOS_OBLIGATORIOS)
    ultimo_documento = documentos.order_by("-fecha_carga").first()

    # ---- Línea de tiempo (4 pasos) ----
    # Cada paso: "hecho", "actual" o "pendiente"
    estado = solicitud.estado if solicitud else None
    finalizada = estado in (Solicitud.APROBADA, Solicitud.RECHAZADA)
    en_evaluacion = estado == Solicitud.EN_EVALUACION
    docs_listos = docs_completos == docs_total

    def paso(nombre, situacion, detalle):
        return {"nombre": nombre, "situacion": situacion, "detalle": detalle}

    if not solicitud:
        pasos = [
            paso("Registro", "hecho", usuario.date_joined),
            paso("Documentos", "pendiente", "Pendiente"),
            paso("Evaluación", "pendiente", "Pendiente"),
            paso("Resultado", "pendiente", "Pendiente"),
        ]
    else:
        pasos = [
            paso("Registro", "hecho", solicitud.fecha_creacion),
            paso(
                "Documentos",
                "hecho" if (docs_listos or en_evaluacion or finalizada) else "actual",
                ultimo_documento.fecha_carga if ultimo_documento else "En proceso",
            ),
            paso(
                "Evaluación",
                "hecho" if finalizada else ("actual" if en_evaluacion else "pendiente"),
                "Finalizada" if finalizada else ("En proceso" if en_evaluacion else "Pendiente"),
            ),
            paso(
                "Resultado",
                "hecho" if finalizada else "pendiente",
                solicitud.get_estado_display() if finalizada else "Pendiente",
            ),
        ]

    # ---- Mensaje del recuadro informativo según el estado ----
    mensajes = {
        None: ("Aún no tienes una solicitud.", "Revisa las convocatorias disponibles y postúlate."),
        Solicitud.PENDIENTE: ("Tu solicitud fue recibida.", "Completa tus documentos para que pase a evaluación."),
        Solicitud.EN_EVALUACION: ("Tu solicitud se encuentra en proceso de evaluación.", "Te notificaremos cuando haya una actualización."),
        Solicitud.APROBADA: ("¡Felicidades! Tu solicitud fue aprobada.", "Pronto recibirás las indicaciones para continuar."),
        Solicitud.RECHAZADA: ("Tu solicitud no fue aprobada.", solicitud.motivo_rechazo if solicitud and solicitud.motivo_rechazo else "Puedes postularte a otra convocatoria disponible."),
    }
    aviso_titulo, aviso_texto = mensajes.get(estado, ("Tu solicitud fue enviada.", "Te notificaremos cuando haya una actualización."))

    # ---- Notificaciones: cambios de estado + documentos subidos ----
    nombres_estado = dict(Solicitud.ESTADOS)
    eventos = []
    if solicitud:
        for h in HistorialEstado.objects.filter(solicitud=solicitud)[:5]:
            eventos.append({
                "titulo": f"Tu solicitud está {nombres_estado.get(h.estado_nuevo, h.estado_nuevo).lower()}",
                "texto": h.comentario or "El estado de tu solicitud cambió.",
                "fecha": h.fecha,
            })
        for d in documentos.order_by("-fecha_carga")[:5]:
            eventos.append({
                "titulo": "Documento recibido",
                "texto": f"{d.get_tipo_display()} se agregó a tu solicitud.",
                "fecha": d.fecha_carga,
            })
    eventos.sort(key=lambda e: e["fecha"], reverse=True)

    return {
        "solicitud": solicitud,
        "estado_texto": solicitud.get_estado_display() if solicitud else "Sin solicitud",
        "pasos": pasos,
        "aviso_titulo": aviso_titulo,
        "aviso_texto": aviso_texto,
        "convocatorias_abiertas": convocatorias_abiertas,
        "docs_completos": docs_completos,
        "docs_total": docs_total,
        "docs_porcentaje": round(docs_completos * 100 / docs_total),
        "notificaciones": eventos[:2],
        "notificaciones_total": len(eventos),
    }
