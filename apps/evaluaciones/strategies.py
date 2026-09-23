"""
Patrón de diseño: STRATEGY (comportamiento)

Problema que resuelve:
    El puntaje final de una solicitud puede calcularse distinto según
    el tipo de beca: un promedio simple entre evaluadores para becas
    de nivel medio, o un promedio ponderado (dando más peso a ciertos
    criterios) para becas universitarias o de posgrado. Sin este
    patrón, esa lógica terminaría en un if/elif dentro del servicio
    de evaluaciones cada vez que se agregue un nuevo tipo de cálculo.

Alternativas consideradas:
    - Un método calcular_puntaje() con if/elif por tipo_beca dentro
      del propio modelo Evaluacion: viola el principio Open/Closed,
      cada tipo nuevo obliga a modificar código ya probado.

Por qué Strategy:
    Cada forma de calcular el puntaje final es una clase
    intercambiable en tiempo de ejecución, seleccionada según el tipo
    de convocatoria, sin condicionales dispersos.

Ventaja para el proyecto:
    Agregar una nueva forma de evaluar (ej. "primero filtrar por
    promedio mínimo de notas") es agregar una clase nueva, sin tocar
    las existentes.
"""

from abc import ABC, abstractmethod


class EstrategiaEvaluacion(ABC):
    @abstractmethod
    def calcular_puntaje_final(self, puntajes: list) -> float:
        ...


class PromedioSimpleStrategy(EstrategiaEvaluacion):
    """Usada para becas de nivel medio: promedio aritmético simple."""

    def calcular_puntaje_final(self, puntajes: list) -> float:
        if not puntajes:
            return 0.0
        return round(sum(puntajes) / len(puntajes), 2)


class PromedioPonderadoStrategy(EstrategiaEvaluacion):
    """
    Usada para becas universitarias/posgrado: da más peso a las
    evaluaciones más altas, penalizando menos una única evaluación baja.
    """

    def calcular_puntaje_final(self, puntajes: list) -> float:
        if not puntajes:
            return 0.0
        puntajes_ordenados = sorted(puntajes, reverse=True)
        pesos = [0.5, 0.3, 0.2][: len(puntajes_ordenados)]
        total_peso = sum(pesos)
        ponderado = sum(p * w for p, w in zip(puntajes_ordenados, pesos))
        return round(ponderado / total_peso, 2)
