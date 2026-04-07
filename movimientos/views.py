from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

from datetime import datetime
import csv
from collections import defaultdict

from asistencia.models import Asistencia, TiempoExtra
from asistencia.utils import calcular_horas_extra_por_rango, calcular_horas_extra_por_dia
from core.models import Incidencia
from core.utils import obtener_empresa_usuario
from core.decorators import solo_operativo, solo_admin


@login_required
def obtener_tiempos_extra(empresa, inicio=None, fin=None, empleado_id=None):

    tiempos = TiempoExtra.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    if inicio and fin:
        tiempos = tiempos.filter(fecha__range=[inicio, fin])

    if empleado_id and empleado_id != "0":
        tiempos = tiempos.filter(empleado_id=empleado_id)

    return tiempos.order_by("fecha")
def exportar_tiempos_extra_csv(request):

    tiempos = obtener_tiempos_extra(
        empresa=request.empresa,
        inicio=request.GET.get("inicio"),
        fin=request.GET.get("fin"),
        empleado_id=request.GET.get("empleado")
    )

    from collections import defaultdict
    import csv
    from django.http import HttpResponse

    por_empleado_dia = defaultdict(list)

    for t in tiempos:
        por_empleado_dia[(t.empleado.nombre, t.fecha)].append(t)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_horas_extra.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha", "Empleado", "Horas Extra"])

    total_general = 0

    for (empleado, fecha), lista in por_empleado_dia.items():
        horas = calcular_horas_extra_por_dia(lista)
        total_general += horas
        writer.writerow([fecha, empleado, horas])

    writer.writerow([])
    writer.writerow(["", "TOTAL GENERAL", total_general])

    return response


@login_required
def lista_movimientos(request):

    empresa = obtener_empresa_usuario(request)

    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    asistencias = Asistencia.objects.filter(empresa=empresa)
    incidencias = Incidencia.objects.filter(empleado__empresa=empresa)
    tiempos_extra = TiempoExtra.objects.filter(asistencia_empresa=empresa)
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)

    total_horas_extra = 0

    if inicio and fecha_fin:

        fecha_inicio_obj = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin_obj = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        asistencias = asistencias.filter(
            fecha__range=(fecha_inicio_obj, fecha_fin_obj)
        )

        incidencias = incidencias.filter(
            fecha_inicio__range=(fecha_inicio_obj, fecha_fin_obj)
        )

        tiempos = TiempoExtra.objects.filter(
            asistencia__empresa=empresa,
            fecha__range=(inicio, fin)
        )
        

        total_horas_extra = calcular_horas_extra_por_rango(tiempos_extra)

        movimientos = obtener_movimientos(
        empresa,
        inicio,
        fin,
        empleado_id
    )

    for a in asistencias:
        movimientos.append({
            "fecha": a.fecha,
            "empleado": a.empleado.nombre,
            "tipo": "ASISTENCIA",
            "detalle": f"Entrada: {a.hora_entrada or '--'} | Salida: {a.hora_salida or '--'}"
        })

    for i in incidencias:
        movimientos.append({
            "fecha": i.fecha_inicio,
            "empleado": i.empleado.nombre,
            "tipo": "INCIDENCIA",
            "detalle": f"{i.tipo} ({i.fecha_inicio} → {i.fecha_fin})"
        })

    for t in tiempos_extra:
        movimientos.append({
            "fecha": t.fecha,
            "empleado": t.empleado.nombre,
            "tipo": "TIEMPO EXTRA",
            "detalle": f"{t.tipo} | {t.hora_inicio} → {t.hora_fin or '--'}"
        })

    movimientos.sort(key=lambda x: x["fecha"], reverse=True)

    context = {
        "movimientos": movimientos,
        "total_horas_extra": total_horas_extra,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }

    return render(request, "movimientos/lista.html", context)
