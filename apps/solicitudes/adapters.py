"""
Patrón de diseño: ADAPTER (estructural)

Problema que resuelve:
    El enunciado del proyecto anticipa que en el futuro el sistema
    deberá integrarse con "otras instituciones" (por ejemplo, para
    validar automáticamente el DPI de un estudiante contra RENAP, o
    verificar notas contra un sistema académico externo). No se
    conoce hoy el formato exacto de esas APIs externas.

Alternativas consideradas:
    - Esperar a que exista la integración real para diseñar algo:
      obliga a modificar el core del sistema (SolicitudService) el
      día que aparezca la integración, arriesgando romper lo ya
      probado.

Por qué Adapter:
    Se define una interfaz propia y estable (ValidadorIdentidadPort)
    que el resto del sistema usa. Cuando exista una API real de una
    institución externa, solo se escribe un Adapter que traduzca esa
    API concreta a la interfaz esperada, sin tocar el resto del código.

Ventaja para el proyecto:
    El sistema queda listo para integraciones futuras (uno de los
    cambios que el propio enunciado adelanta) sin sobre-diseñar hoy
    algo que todavía no existe.
"""

from abc import ABC, abstractmethod


class ValidadorIdentidadPort(ABC):
    """Interfaz que el sistema espera para validar identidad de un estudiante."""

    @abstractmethod
    def validar(self, cui: str) -> bool:
        ...


class ValidadorIdentidadSimulado(ValidadorIdentidadPort):
    """
    Implementación provisional usada mientras no exista integración
    real con una institución externa (ej. RENAP). Simplemente valida
    el formato del CUI. El día que exista la API real, se crea un
    nuevo Adapter (ej. ValidadorRenapAdapter) que implemente la misma
    interfaz sin cambiar quién la consume.
    """

    def validar(self, cui: str) -> bool:
        return cui.isdigit() and len(cui) == 13
