from asistencia.models import Asistencia
from core.services.asistencia_service import obtener_tiempo_extra


def obtener_resultados_tiempo_extra(
    empresa,
    inicio=None,
    fin=None,
    empleado_id=None,
):
    asistencias = (
        Asistencia.objects
        .filter(empleado__empresa=empresa)
        .select_related("empleado")
    )

    if inicio and fin:
        asistencias = asistencias.filter(
            fecha__range=(inicio, fin),
        )
    elif inicio:
        asistencias = asistencias.filter(
            fecha__gte=inicio,
        )
    elif fin:
        asistencias = asistencias.filter(
            fecha__lte=fin,
        )

    if empleado_id and empleado_id not in ["", "0"]:
        asistencias = asistencias.filter(
            empleado_id=empleado_id,
        )

    asistencias = asistencias.order_by(
        "empleado__numero_empleado",
        "fecha",
    )

    resultados = []
    total_horas = 0

    for asistencia in asistencias:
        info = obtener_tiempo_extra(asistencia)

        if not info:
            continue

        horas = info.get("horas", 0)

        resultados.append({
            "empleado": asistencia.empleado,
            "fecha": asistencia.fecha,
            "hora_inicio": info.get("inicio"),
            "hora_fin": info.get("fin"),
            "horas": horas,
        })

        if isinstance(horas, (int, float)):
            total_horas += horas

    return resultados, total_horas