from asistencia.models import Asistencia
from core.models import Incidencia


def obtener_asistencias_base(request):
    empresa = request.empresa

    return (
        Asistencia.objects
        .filter(empleado__empresa=empresa)
        .select_related("empleado")
    )


def aplicar_filtros_asistencia(request, queryset):
    empleado_id = request.GET.get("empleado")
    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    if empleado_id and empleado_id not in ["", "0"]:
        queryset = queryset.filter(
            empleado_id=empleado_id,
        )

    if inicio:
        queryset = queryset.filter(
            fecha__gte=inicio,
        )

    if fin:
        queryset = queryset.filter(
            fecha__lte=fin,
        )

    return queryset


def calcular_incidencias_asistencia(empleado, fecha):
    incidencias = []

    incidencias_qs = Incidencia.objects.filter(
        empleado=empleado,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha,
    )

    for incidencia in incidencias_qs:
        incidencias.append(
            incidencia.tipo
            if hasattr(incidencia, "tipo")
            else "INCIDENCIA"
        )

    return incidencias