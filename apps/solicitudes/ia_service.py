from django.conf import settings
from google import genai
from google.genai import types

class GeminiService:
    """
    Servicio encargado de mejorar la redacción
    del motivo de una solicitud de beca.

    La IA únicamente mejora la forma del texto.
    No debe inventar información que el estudiante
    no haya proporcionado.
    """

    @staticmethod
    def mejorar_motivo(texto: str) -> str:
        texto = texto.strip()

        if not texto:
            raise ValueError(
                "Debe proporcionar un texto para mejorar."
            )

        if len(texto) > 1000:
            raise ValueError(
                "El motivo no puede superar los 1000 caracteres."
            )

        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "La API key de Gemini no está configurada."
            )

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        instrucciones = """
Eres un asistente de redacción para un sistema de becas estudiantiles.

Tu tarea es mejorar únicamente la redacción del motivo escrito por
el estudiante.

Reglas obligatorias:

1. Conserva el significado original.
2. Usa un tono formal, claro, humano y respetuoso.
3. Corrige ortografía, gramática y puntuación.
4. No inventes información.
5. No inventes ingresos económicos.
6. No inventes problemas familiares.
7. No inventes calificaciones, méritos o logros académicos.
8. No inventes situaciones personales.
9. No agregues datos que el estudiante no haya mencionado.
10. No prometas que la beca será aprobada.
11. No evalúes al estudiante.
12. No agregues encabezados como "Motivo mejorado".
13. Devuelve únicamente el texto mejorado.
14. Mantén una extensión similar al texto original.
15. Escribe en español.

Si el texto original es breve, mejóralo sin agregar hechos nuevos.
"""

        # Limpiamos cualquier salto de línea o espacio invisible de Windows
        modelo_limpio = settings.GEMINI_MODEL.strip() if settings.GEMINI_MODEL else "gemini-1.5-flash"

        response = client.models.generate_content(
            model="gemini-3.8-flash",  # ¡La versión correcta que pide Google!
            contents=texto,
            config=types.GenerateContentConfig(
                system_instruction=instrucciones,
                max_output_tokens=500,
            ),
        )
        
        texto_mejorado = (response.text or "").strip()

        if not texto_mejorado:
            raise RuntimeError(
                "Gemini no devolvió ningún texto."
            )

        return texto_mejorado