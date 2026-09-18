"""
Patrón de diseño: FACTORY METHOD (creacional)

Problema que resuelve:
    Decidir QUÉ estrategia de cálculo de puntaje usar (Strategy, ver
    strategies.py) depende del tipo de beca de la convocatoria. Ese
    "if/elif de creación" no debería repetirse en cada lugar del
    código que necesite una estrategia.

Alternativas consideradas:
    - Instanciar la estrategia directamente donde se necesite
      (ej. en la vista): duplica la regla de mapeo tipo->estrategia
      en varios lugares y dificulta agregar un tipo de beca nuevo.

Por qué Factory Method:
    Centraliza la creación del objeto Strategy correcto en un único
    punto, separando "cómo se crea" de "cómo se usa".

Ventaja para el proyecto:
    Agregar un nuevo tipo de beca con su propia forma de evaluar es
    un cambio de una línea en esta fábrica, no una búsqueda de todos
    los lugares donde se instancia una estrategia.
"""

from .strategies import EstrategiaEvaluacion, PromedioPonderadoStrategy, PromedioSimpleStrategy


class EstrategiaEvaluacionFactory:
    """Fábrica que devuelve la estrategia de evaluación según el tipo de beca."""

    _MAPA = {
        "MEDIO": PromedioSimpleStrategy,
        "UNIVERSITARIO": PromedioPonderadoStrategy,
        "POSGRADO": PromedioPonderadoStrategy,
    }

    @classmethod
    def crear(cls, tipo_beca: str) -> EstrategiaEvaluacion:
        estrategia_cls = cls._MAPA.get(tipo_beca, PromedioSimpleStrategy)
        return estrategia_cls()
