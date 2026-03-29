from django.contrib import admin
from .models import Empleado



@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):

    list_display = (
        "numero_empleado",
        "nombre",
        "departamento",
        "activo",
        "control_horario",
    )

    list_display_links = (
        "nombre",
    )

    list_filter = (
        "control_horario",
        "activo",
        "departamento",
    )

    search_fields = (
        "nombre",
        "numero_empleado",
    )


