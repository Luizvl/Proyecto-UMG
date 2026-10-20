from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.usuarios.models import Usuario

from .ia_service import GeminiService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mejorar_motivo_ia(request):
    """
    Mejora mediante Gemini la redacción del motivo
    escrito por un estudiante.

    Espera:
    {
        "texto": "motivo escrito por el estudiante"
    }

    Devuelve:
    {
        "texto_mejorado": "versión mejor redactada"
    }
    """

    # Esta herramienta está destinada a estudiantes.
    if (
        request.user.rol != Usuario.Rol.ESTUDIANTE
        and not request.user.is_superuser
    ):
        return Response(
            {
                "detail": (
                    "Esta herramienta está disponible "
                    "únicamente para estudiantes."
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    texto = request.data.get("texto", "")

    if not isinstance(texto, str):
        return Response(
            {
                "detail": "El campo texto debe ser una cadena de texto."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    texto = texto.strip()

    if not texto:
        return Response(
            {
                "detail": "Debe escribir un motivo antes de mejorarlo."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(texto) > 1000:
        return Response(
            {
                "detail": (
                    "El motivo no puede superar "
                    "los 1000 caracteres."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        texto_mejorado = GeminiService.mejorar_motivo(
            texto
        )

    except ValueError as exc:
        return Response(
            {
                "detail": str(exc)
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except RuntimeError:
        return Response(
            {
                "detail": (
                    "El servicio de inteligencia artificial "
                    "no está disponible temporalmente."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except Exception:
        # Evitamos mostrar al usuario datos internos
        # provenientes de la API externa.
        return Response(
            {
                "detail": (
                    "No fue posible mejorar el texto "
                    "en este momento. Intente nuevamente."
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(
        {
            "texto_mejorado": texto_mejorado
        },
        status=status.HTTP_200_OK,
    )