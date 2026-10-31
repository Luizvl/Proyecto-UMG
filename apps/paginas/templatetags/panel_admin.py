"""
Etiquetas de plantilla SOLO para la presentación del panel de administración.
No cambian datos, permisos ni reglas: leen la base de datos y preparan lo que
se dibuja en el menú lateral, el dashboard y las tarjetas de cada lista.
Uso:  {% load panel_admin %}
"""
from django import template
from django.apps import apps
from django.db.models import Avg, Count
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

register = template.Library()

# Orden del menú: (app_label, modelo, texto, icono, sección)
MENU = [
    ("usuarios", "usuario", "Usuarios", "usuario", "Gestión"),
    ("convocatorias", "convocatoria", "Convocatorias", "convocatorias", "Gestión"),
    ("solicitudes", "solicitud", "Solicitudes", "documento_solicitudes", "Gestión"),
    ("evaluaciones", "evaluacion", "Evaluaciones", "evaluaciones", "Gestión"),
    ("evaluaciones", "comite", "Comités evaluadores", "grupos_comites", "Gestión"),
    ("pagos", "pago", "Pagos", "pagos", "Pagos"),
    ("pagos", "condicionpago", "Condiciones de pago", "configuracion", "Pagos"),
    ("solicitudes", "auditoriasolicitud", "Auditoría", "auditoria", "Sistema"),
    ("auth", "group", "Grupos y permisos", "clave_permisos", "Sistema"),
]

COLORES_SOLICITUD = {
    "PENDIENTE": "#f59e0b",
    "EN_EVALUACION": "#3b82f6",
    "PENDIENTE_SEGUNDA_APROBACION": "#8b5cf6",
    "APROBADA": "#10b981",
    "RECHAZADA": "#ef4444",
}


def _modelo(app_label, nombre):
    try:
        return apps.get_model(app_label, nombre)
    except LookupError:
        return None


@register.simple_tag
def menu_admin(available_apps, ruta):
    """Arma el menú lateral respetando los permisos que Django ya calculó."""
    permitidos = {}
    for app in available_apps or []:
        for m in app["models"]:
            permitidos[(app["app_label"], m["object_name"].lower())] = m

    secciones = {}
    usados = set()
    for app_label, modelo, texto, icono, seccion in MENU:
        m = permitidos.get((app_label, modelo))
        if not m or not m.get("admin_url"):
            continue
        usados.add((app_label, modelo))
        secciones.setdefault(seccion, []).append({
            "texto": texto, "icono": icono, "url": m["admin_url"],
            "activo": ruta.startswith(m["admin_url"]),
        })
    # Cualquier modelo nuevo que registren los compañeros también aparece
    for clave, m in permitidos.items():
        if clave not in usados and m.get("admin_url"):
            secciones.setdefault("Otros", []).append({
                "texto": m["name"], "icono": "plantillas", "url": m["admin_url"],
                "activo": ruta.startswith(m["admin_url"]),
            })
    orden = ["Gestión", "Pagos", "Sistema", "Otros"]
    return [(s, secciones[s]) for s in orden if s in secciones]


def _url(nombre, *args):
    try:
        return reverse(nombre, args=args)
    except NoReverseMatch:
        return ""


@register.simple_tag
def datos_dashboard():
    Usuario = _modelo("usuarios", "Usuario")
    Convocatoria = _modelo("convocatorias", "Convocatoria")
    Solicitud = _modelo("solicitudes", "Solicitud")
    Comite = _modelo("evaluaciones", "Comite")
    Evaluacion = _modelo("evaluaciones", "Evaluacion")
    hoy = timezone.localdate()

    # ---- Tarjetas ----
    usuarios = Usuario.objects.count()
    estudiantes = Usuario.objects.filter(rol="ESTUDIANTE").count()
    convocatorias = Convocatoria.objects.count()
    abiertas = sum(1 for c in Convocatoria.objects.all() if c.esta_abierta())
    solicitudes = Solicitud.objects.count()
    pendientes = Solicitud.objects.filter(estado="PENDIENTE").count()
    comites = Comite.objects.count()
    integrantes = Usuario.objects.filter(comites__isnull=False).distinct().count()

    tarjetas = [
        {"titulo": "Usuarios", "valor": usuarios, "icono": "usuario", "color": "azul",
         "detalle": f"{estudiantes} estudiante{'s' if estudiantes != 1 else ''}",
         "url": _url("admin:usuarios_usuario_changelist")},
        {"titulo": "Convocatorias", "valor": convocatorias, "icono": "convocatorias", "color": "verde",
         "detalle": f"{abiertas} abierta{'s' if abiertas != 1 else ''} hoy",
         "url": _url("admin:convocatorias_convocatoria_changelist")},
        {"titulo": "Solicitudes", "valor": solicitudes, "icono": "documento_solicitudes", "color": "naranja",
         "detalle": f"{pendientes} pendiente{'s' if pendientes != 1 else ''}",
         "url": _url("admin:solicitudes_solicitud_changelist")},
        {"titulo": "Comités", "valor": comites, "icono": "grupos_comites", "color": "morado",
         "detalle": f"{integrantes} integrante{'s' if integrantes != 1 else ''}",
         "url": _url("admin:evaluaciones_comite_changelist")},
    ]

    # ---- Gráfica de solicitudes por estado (dona con datos reales) ----
    conteo = dict(Solicitud.objects.values_list("estado").annotate(n=Count("id")))
    estados, tramos, acumulado = [], [], 0.0
    lista_url = _url("admin:solicitudes_solicitud_changelist")
    for clave, etiqueta in Solicitud.ESTADOS:
        n = conteo.get(clave, 0)
        pct = (n * 100 / solicitudes) if solicitudes else 0
        color = COLORES_SOLICITUD.get(clave, "#94a3b8")
        estados.append({"etiqueta": etiqueta, "n": n, "pct": round(pct), "color": color,
                        "url": f"{lista_url}?estado__exact={clave}"})
        if n:
            tramos.append(f"{color} {acumulado:.2f}% {acumulado + pct:.2f}%")
            acumulado += pct
    dona = f"conic-gradient({', '.join(tramos)})" if tramos else "conic-gradient(#e5e9f2 0 100%)"

    # ---- Convocatorias recientes ----
    recientes = []
    for c in Convocatoria.objects.annotate(n=Count("solicitudes")).order_by("-fecha_inicio")[:5]:
        if c.esta_abierta():
            clave, etiqueta = "activa", "Abierta"
        elif c.estado == c.ESTADO_ACTIVA and c.fecha_inicio > hoy:
            clave, etiqueta = "proxima", "Próxima"
        elif c.estado == c.ESTADO_ACTIVA:
            clave, etiqueta = "vencida", "Vencida"
        else:
            clave, etiqueta = "cerrada", "Cerrada"
        recientes.append({
            "obj": c, "tipo": c.get_tipo_beca_display(), "n": c.n,
            "clave": clave, "etiqueta": etiqueta,
            "ocupacion": min(round(c.n * 100 / c.cupo), 100) if c.cupo else 0,
            "url": _url("admin:convocatorias_convocatoria_change", c.pk),
        })

    # ---- Solicitudes recientes ----
    ultimas = [{
        "obj": s, "estado": s.get_estado_display(), "clave": s.estado.lower(),
        "url": _url("admin:solicitudes_solicitud_change", s.pk),
    } for s in Solicitud.objects.select_related("estudiante", "convocatoria")[:5]]

    promedio = Evaluacion.objects.aggregate(p=Avg("puntaje"))["p"]
    Pago = _modelo("pagos", "Pago")
    pagos_revision = Pago.objects.filter(estado="pendiente").count() if Pago else None

    return {
        "tarjetas": tarjetas, "estados": estados, "dona": dona, "total_solicitudes": solicitudes,
        "recientes": recientes, "ultimas": ultimas,
        "evaluaciones": Evaluacion.objects.count(),
        "pagos_revision": pagos_revision,
        "promedio": round(promedio, 1) if promedio is not None else None,
        "hoy": hoy,
    }


@register.simple_tag
def resumen_lista(opts):
    """Tarjetas de resumen que se muestran arriba de cada lista del admin."""
    Modelo = opts.model
    clave = f"{opts.app_label}.{opts.model_name}"
    base = _url(f"admin:{opts.app_label}_{opts.model_name}_changelist")
    total = Modelo.objects.count()
    tarjetas = [{"titulo": f"Total de {opts.verbose_name_plural.lower()}", "valor": total,
                 "color": "azul", "url": base}]

    if clave == "convocatorias.convocatoria":
        todas = list(Modelo.objects.all())
        abiertas = sum(1 for c in todas if c.esta_abierta())
        cerradas = sum(1 for c in todas if c.estado == "CERRADA")
        tarjetas += [
            {"titulo": "Abiertas hoy", "valor": abiertas, "color": "verde",
             "url": f"{base}?estado__exact=ACTIVA"},
            {"titulo": "Cerradas", "valor": cerradas, "color": "rojo",
             "url": f"{base}?estado__exact=CERRADA"},
            {"titulo": "Cupos ofrecidos", "valor": sum(c.cupo for c in todas), "color": "morado", "url": ""},
        ]
    elif clave == "solicitudes.solicitud":
        conteo = dict(Modelo.objects.values_list("estado").annotate(n=Count("id")))
        colores = {"PENDIENTE": "naranja", "EN_EVALUACION": "azul", "PENDIENTE_SEGUNDA_APROBACION": "morado",
                   "APROBADA": "verde", "RECHAZADA": "rojo"}
        for valor, etiqueta in Modelo.ESTADOS:
            tarjetas.append({"titulo": etiqueta, "valor": conteo.get(valor, 0),
                             "color": colores.get(valor, "azul"), "url": f"{base}?estado__exact={valor}"})
    elif clave == "usuarios.usuario":
        conteo = dict(Modelo.objects.values_list("rol").annotate(n=Count("id")))
        colores = {"ESTUDIANTE": "verde", "COMITE": "morado", "ADMINISTRADOR": "naranja"}
        for valor, etiqueta in Modelo.Rol.choices:
            tarjetas.append({"titulo": etiqueta if valor != "COMITE" else "Comité", "valor": conteo.get(valor, 0),
                             "color": colores.get(valor, "azul"), "url": f"{base}?rol__exact={valor}"})
    elif clave == "pagos.pago":
        conteo = dict(Modelo.objects.values_list("estado").annotate(n=Count("id")))
        colores = {"pendiente": "naranja", "aprobado": "verde", "rechazado": "rojo"}
        for valor, etiqueta in Modelo.ESTADOS_PAGO:
            tarjetas.append({"titulo": etiqueta, "valor": conteo.get(valor, 0),
                             "color": colores.get(valor, "azul"), "url": f"{base}?estado__exact={valor}"})
    elif clave == "evaluaciones.evaluacion":
        prom = Modelo.objects.aggregate(p=Avg("puntaje"))["p"]
        tarjetas.append({"titulo": "Puntaje promedio", "valor": round(prom, 1) if prom is not None else "—",
                         "color": "verde", "url": ""})
    elif clave == "evaluaciones.comite":
        Usuario = _modelo("usuarios", "Usuario")
        tarjetas.append({"titulo": "Integrantes", "color": "morado", "url": "",
                         "valor": Usuario.objects.filter(comites__isnull=False).distinct().count()})
    return tarjetas
