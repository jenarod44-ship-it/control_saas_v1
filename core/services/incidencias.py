from datetime import timedelta, datetime
from core.models import IncidenciaDia
from asistencia.models import Asistencia


def generar_incidencias_por_rango(incidencia):
    from asistencia.models import Asistencia  # 👈 aquí

    ...
    fecha = incidencia.fecha_inicio
    fecha_fin = incidencia.fecha_fin

    if isinstance(fecha, str):
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()

    if isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    while fecha <= fecha_fin:

        IncidenciaDia.objects.get_or_create(
            empleado=incidencia.empleado,
            fecha=fecha,
            defaults={
                "tipo": incidencia.tipo,
                "incidencia": incidencia
            }
        )

        asistencia, _ = Asistencia.objects.get_or_create(
            empresa=incidencia.empresa,  # ⚠️ IMPORTANTE (por tu unique_together)
            empleado=incidencia.empleado,
            fecha=fecha
        )

        # ✅ AQUÍ ESTÁ EL FIX REAL
        asistencia.tipo_dia = incidencia.tipo
        asistencia.save()

        fecha += timedelta(days=1)
