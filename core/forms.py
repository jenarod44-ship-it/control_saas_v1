from django import forms
from .models import Incidencia


class IncidenciaForm(forms.ModelForm):

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)

        print(self.fields)

        if empresa:
            self.fields["empleado"].queryset = Empleado.objects.all()
                
             
            

    class Meta:
        model = Incidencia
        fields = ["empleado", "tipo", "fecha_inicio", "fecha_fin"]

        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }