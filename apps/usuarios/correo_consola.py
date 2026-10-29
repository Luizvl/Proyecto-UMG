"""
Backend de correo para DESARROLLO.

En lugar de enviar el correo, lo imprime en la terminal de
"python manage.py runserver" de forma legible (con tildes y el enlace
completo en una sola línea), para poder copiar el enlace de
recuperación de contraseña sin necesidad de un servidor de correo.
"""
from django.core.mail.backends.console import EmailBackend as ConsolaBase


class EmailBackend(ConsolaBase):
    def write_message(self, message):
        separador = "=" * 70
        self.stream.write(
            f"\n{separador}\n"
            f"  CORREO (modo desarrollo, no se envió de verdad)\n"
            f"  Para:   {', '.join(message.to)}\n"
            f"  Asunto: {message.subject}\n"
            f"{separador}\n\n"
            f"{message.body}\n"
            f"{separador}\n\n"
        )
