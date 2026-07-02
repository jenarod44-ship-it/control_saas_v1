from django.contrib import admin
from .models import Departamento, Empleado


# ========================
# DEPARTAMENTO
# ========================
@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = (
        "empresa",
        "nombre",
        "activo",
        "trabaja_fines_semana",
    )

    search_fields = (
        "nombre",
        "empresa__nombre",
    )

    list_filter = (
        "empresa",
        "activo",
        "trabaja_fines_semana",
    )

    ordering = (
        "empresa__nombre",
        "nombre",
    )


# ========================
# EMPLEADO
# ========================
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_empleado",
        "nombre",
        "empresa",
        "departamento",
        "turno",
        "control_horario",
        "activo",
        "costo_hora",
    )

    search_fields = (
        "numero_empleado",
        "nombre",
        "empresa__nombre",
        "departamento__nombre",
        "turno__nombre",
    )

    list_filter = (
        "empresa",
        "departamento",
        "turno",
        "control_horario",
        "activo",
    )

    ordering = (
        "empresa__nombre",
        "numero_empleado",
    )

    fieldsets = (
        ("Datos del empleado", {
            "fields": (
                "empresa",
                "numero_empleado",
                "nombre",
                "activo",
            )
        }),
        ("Organización", {
            "fields": (
                "departamento",
                "turno",
            )
        }),
        ("Control de asistencia", {
            "fields": (
                "control_horario",
                "dias_trabajo",
            )
        }),
        ("Costo", {
            "fields": (
                "costo_hora",
            )
        }),
    )
