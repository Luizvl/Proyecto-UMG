from django import forms

from .models import Pago


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["comprobante"]
        widgets = {
            "comprobante": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_comprobante(self):
        archivo = self.cleaned_data["comprobante"]
        if archivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La imagen no debe superar 5 MB.")
        return archivo