from core.models import Incidencia


def obtener_incidencias(
    empresa,
    inicio=None,
    fin=None,
    empleado_id=None,
):
    incidencias = (
        Incidencia.objects
        .filter(empleado__empresa=empresa)
        .select_related("empleado")
    )

    if inicio:
        incidencias = incidencias.filter(
            fecha_inicio__gte=inicio,
        )

    if fin:
        incidencias = incidencias.filter(
            fecha_inicio__lte=fin,
        )

    if empleado_id and empleado_id != "0":
        incidencias = incidencias.filter(
            empleado_id=empleado_id,
        )

    return incidencias.order_by(
        "empleado__numero_empleado",
        "-fecha_inicio",
    )