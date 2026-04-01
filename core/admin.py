from django.contrib import admin
from .models import Turno, Incidencia
from .models import Empresa

admin.site.register(Empresa)


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "empresa",
        "hora_entrada",
        "hora_salida",
        "tolerancia_minutos",
        "activo",
    )



@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("empleado", "tipo", "fecha_inicio", "fecha_fin")
    list_filter = ("tipo", "fecha_inicio")


    