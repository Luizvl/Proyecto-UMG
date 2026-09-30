"""
Patrón de diseño: BUILDER (creacional)

Problema que resuelve:
    Una solicitud "completa" no es solo el registro en la tabla
    Solicitud: normalmente se arma junto con uno o más documentos de
    respaldo, y ese conjunto de datos puede llegar en pasos distintos
    (el estudiante llena datos, luego sube DPI, luego constancia,
    etc.) antes de confirmarse. Construir todo eso en un único
    constructor con muchos parámetros sería confuso y frágil ante
    campos opcionales.

Alternativas consideradas:
    - Un método crear_solicitud(estudiante, convocatoria, doc1=None,
      doc2=None, doc3=None, ...) con muchos parámetros opcionales:
      difícil de leer y de extender.

Por qué Builder:
    Permite construir la solicitud paso a paso (agregar documento por
    documento) y confirmar la creación al final, validando que estén
    los datos mínimos antes de persistir.

Ventaja para el proyecto:
    El flujo de "llenar solicitud en varios pasos" del formulario del
    estudiante se modela de forma natural, sin acoplar la vista a los
    detalles de creación de Documento y Solicitud.
"""

from django.core.exceptions import ValidationError

from .services import SolicitudService


class SolicitudBuilder:
    def __init__(self, estudiante, convocatoria):
        self._estudiante = estudiante
        self._convocatoria = convocatoria
        self._documentos_pendientes = []  # lista de (archivo, tipo)

    def con_documento(self, archivo, tipo: str) -> "SolicitudBuilder":
        self._documentos_pendientes.append((archivo, tipo))
        return self  # permite encadenar: builder.con_documento(...).con_documento(...)

    def construir(self):
        if not self._documentos_pendientes:
            raise ValidationError(
                "Debe adjuntar al menos un documento antes de enviar la solicitud."
            )

        solicitud = SolicitudService.crear_solicitud(self._estudiante, self._convocatoria)
        for archivo, tipo in self._documentos_pendientes:
            SolicitudService.agregar_documento(solicitud, archivo, tipo)
        return solicitud
