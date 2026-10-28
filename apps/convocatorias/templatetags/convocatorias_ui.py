"""
Etiquetas de plantilla SOLO para la presentación del listado de convocatorias.
No cambian datos ni reglas: leen cada convocatoria y calculan lo que se muestra.
Uso:  {% load convocatorias_ui %}
"""
from django import template

register = template.Library()

IMAGENES = {
    "UNIVERSITARIO": "img/conv-universitario.webp",
    "MEDIO": "img/conv-medio.webp",
    "POSGRADO": "img/conv-posgrado.webp",
}


@register.simple_tag
def datos_convocatoria(convocatoria, usuario):
    ocupados = convocatoria.solicitudes.count()
    disponibles = max(convocatoria.cupo - ocupados, 0)
    abierta = convocatoria.esta_abierta()
    ya_aplico = (
        usuario.is_authenticated
        and convocatoria.solicitudes.filter(estudiante=usuario).exists()
    )
    if abierta:
        clave, etiqueta = "activa", "Activa"
    elif convocatoria.estado == convocatoria.ESTADO_ACTIVA:
        clave, etiqueta = "proxima", "Fuera de fecha"
    else:
        clave, etiqueta = "cerrada", "Cerrada"
    return {
        "disponibles": disponibles,
        "porcentaje": round(disponibles * 100 / convocatoria.cupo) if convocatoria.cupo else 0,
        "abierta": abierta,
        "sin_cupo": disponibles == 0,
        "ya_aplico": ya_aplico,
        "clave": clave,
        "etiqueta": etiqueta,
        "imagen": IMAGENES.get(convocatoria.tipo_beca, "img/conv-universitario.webp"),
    }
