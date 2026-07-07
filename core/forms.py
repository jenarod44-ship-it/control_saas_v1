from django import forms
from .models import Incidencia
from nucleo.models import Empleado


class IncidenciaForm(forms.ModelForm):

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields["empleado"].queryset = Empleado.objects.filter(
                empresa=empresa,
                activo=True
            ).order_by("numero_empleado", "nombre")
        else:
            self.fields["empleado"].queryset = Empleado.objects.none()

    class Meta:
        model = Incidencia
        fields = ["empleado", "tipo", "fecha_inicio", "fecha_fin"]

        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }