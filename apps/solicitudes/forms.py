from django import forms
from .models import Solicitud

class SolicitudForm(forms.ModelForm):
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Explica brevemente por qué solicitas esta beca...',
            'required': True
        }),
        label="Motivo de la Solicitud"
    )
    documento = forms.FileField(
        widget=forms.FileInput(attrs={
            'accept': '.pdf',
            'required': True
        }),
        label="Documento de Respaldo (PDF)",
        help_text="Sube un único archivo PDF con tu constancia de estudios o DPI."
    )

    class Meta:
        model = Solicitud
        fields = ['motivo', 'documento']