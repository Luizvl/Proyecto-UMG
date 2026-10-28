"""
Etiquetas de plantilla SOLO para la presentación de "Mis solicitudes".

No cambian datos ni reglas de negocio: leen las solicitudes que la vista
ya envía y calculan textos, colores y pasos para mostrarlos de forma clara.
Uso en la plantilla:   {% load solicitudes_ui %}
"""
from django import template

register = template.Library()

DOCUMENTOS_OBLIGATORIOS = ["DPI", "CONSTANCIA_ESTUDIOS", "NOTAS"]


def _docs(solicitud):
    tipos = set(solicitud.documentos.values_list("tipo", flat=True))
    completos = [t for t in DOCUMENTOS_OBLIGATORIOS if t in tipos]
    return len(completos), len(DOCUMENTOS_OBLIGATORIOS)


@register.simple_tag
def resumen_solicitud(solicitud):
    """Devuelve todo lo que la tarjeta de una solicitud necesita mostrar."""
    estado = solicitud.estado
    docs_ok, docs_total = _docs(solicitud)
    docs_listos = docs_ok == docs_total
    finalizada = estado in ("APROBADA", "RECHAZADA")
    en_evaluacion = estado == "EN_EVALUACION"

    # Etiqueta y color del estado (clave usada también para filtrar)
    if estado == "APROBADA":
        clave, etiqueta = "aprobada", "Aprobada"
    elif estado == "RECHAZADA":
        clave, etiqueta = "rechazada", "Rechazada"
    elif en_evaluacion:
        clave, etiqueta = "evaluacion", "En evaluación"
    elif not docs_listos:
        clave, etiqueta = "pendiente", "Documentos pendientes"
    else:
        clave, etiqueta = "pendiente", "Pendiente de revisión"

    def paso(nombre, situacion):
        return {"nombre": nombre, "situacion": situacion}

    pasos = [
        paso("Registro", "hecho"),
        paso("Documentos", "hecho" if (docs_listos or en_evaluacion or finalizada) else "actual"),
        paso("Evaluación", "hecho" if finalizada else ("actual" if en_evaluacion else "pendiente")),
        paso("Resultado", ("hecho" if estado == "APROBADA" else "rechazado") if finalizada else "pendiente"),
    ]

    return {
        "clave": clave,
        "etiqueta": etiqueta,
        "pasos": pasos,
        "docs_ok": docs_ok,
        "docs_total": docs_total,
        # Solo se piden documentos mientras la solicitud no ha pasado a evaluación
        "docs_pendientes": not docs_listos and not finalizada and not en_evaluacion,
        "documentos": list(solicitud.documentos.all()),
        "historial": list(solicitud.historial.all()[:4]),
    }


@register.simple_tag
def resumen_general(solicitudes):
    """Conteos de las tarjetas de arriba, próximas acciones y últimas actualizaciones."""
    solicitudes = list(solicitudes)
    conteo = {"total": len(solicitudes), "evaluacion": 0, "aprobada": 0, "pendiente": 0, "rechazada": 0}
    acciones, eventos = [], []
    nombres = {"PENDIENTE": "pendiente", "EN_EVALUACION": "en evaluación", "APROBADA": "aprobada", "RECHAZADA": "rechazada"}

    for s in solicitudes:
        r = resumen_solicitud(s)
        conteo[r["clave"]] += 1
        nombre = s.convocatoria.nombre
        if r["docs_pendientes"]:
            acciones.append({"tipo": "alerta", "titulo": "Subir documentos", "beca": nombre,
                             "texto": f"Tienes {r['docs_total'] - r['docs_ok']} documento(s) pendiente(s) por enviar."})
        elif r["clave"] == "evaluacion":
            acciones.append({"tipo": "info", "titulo": "Revisar resultado", "beca": nombre,
                             "texto": "Te notificaremos cuando haya una actualización."})
        for h in r["historial"]:
            eventos.append({"titulo": f"Tu solicitud está {nombres.get(h.estado_nuevo, h.estado_nuevo.lower())}",
                            "beca": nombre, "fecha": h.fecha, "clave": h.estado_nuevo.lower()})
        for d in r["documentos"]:
            eventos.append({"titulo": "Documento recibido", "beca": nombre, "fecha": d.fecha_carga, "clave": "documento"})
        if r["docs_pendientes"] and not r["documentos"]:
            eventos.append({"titulo": "Documentos pendientes", "beca": nombre, "fecha": s.fecha_creacion, "clave": "pendiente"})

    eventos.sort(key=lambda e: e["fecha"], reverse=True)
    return {"conteo": conteo, "acciones": acciones[:2], "eventos": eventos[:3]}


@register.filter
def nombre_estado(clave):
    """Convierte 'EN_EVALUACION' en 'En evaluación' para mostrarlo."""
    nombres = {"PENDIENTE": "Pendiente", "EN_EVALUACION": "En evaluación",
               "APROBADA": "Aprobada", "RECHAZADA": "Rechazada"}
    return nombres.get(clave, str(clave).replace("_", " ").capitalize())
