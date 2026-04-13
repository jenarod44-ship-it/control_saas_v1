from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import csv
from collections import defaultdict
from core.models import Incidencia
from core.decorators import solo_operativo, solo_admin



@login_required
def exportar_tiempos_extra_csv(request):

    from asistencia.models import Asistencia, Movimiento
    from django.http import HttpResponse
    import csv

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    asistencias = Asistencia.objects.filter(
        empleado__empresa=request.empresa
    ).select_related("empleado")

    # 🔥 FILTRO POR FECHA (CORRECTO)
    if inicio and fin:
        asistencias = asistencias.filter(fecha__range=[inicio, fin])
    elif inicio:
        asistencias = asistencias.filter(fecha__gte=inicio)
    elif fin:
        asistencias = asistencias.filter(fecha__lte=fin)

    # 🔥 FILTRO POR EMPLEADO
    if empleado_id and empleado_id != "0":
        asistencias = asistencias.filter(empleado_id=empleado_id)

    # 🔥 ORDEN (IMPORTANTE)
    asistencias = asistencias.order_by("empleado__nombre", "fecha")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_horas_extra.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha", "Empleado", "Horas Extra"])

    total_general = 0

    for a in asistencias:

        movimientos = Movimiento.objects.filter(
            asistencia=a
        ).order_by("hora")

        inicio_extra = None
        fin_extra = None

        for m in movimientos:
            if m.tipo == "INICIO_TIEMPO_EXTRA":
                inicio_extra = m.hora
            elif m.tipo == "FIN_TIEMPO_EXTRA":
                fin_extra = m.hora

        if inicio_extra:

            if fin_extra:
                t_inicio = datetime.combine(a.fecha, inicio_extra)
                t_fin = datetime.combine(a.fecha, fin_extra)

                diff = t_fin - t_inicio

                total_minutos = int(diff.total_seconds() / 60)

                horas_base = total_minutos // 60
                minutos = total_minutos % 60

                # 🔥 REGLA DE NEGOCIO
                if minutos >= 45:
                    horas_final = horas_base + 1
                else:
                    horas_final = horas_base

                total_general += horas_final

                writer.writerow([
                    a.fecha,
                    a.empleado.nombre,
                    horas_final
                ])

            else:
                # 🔥 EN CURSO
                writer.writerow([
                    a.fecha,
                    a.empleado.nombre,
                    "EN CURSO"
                ])
    

    return response

@login_required
def lista_movimientos(request):

    empresa = request.empresa

    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    incidencias = Incidencia.objects.filter(
        empleado__empresa=empresa
    )
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

        asistencias = Asistencia.objects.filter(
            empleado__empresa=empresa
        ).select_related("empleado")

        if inicio and fin:
            asistencias = asistencias.filter(fecha__range=(inicio, fin))
        elif inicio:
            asistencias = asistencias.filter(fecha__gte=inicio)
        elif fin:
            asistencias = asistencias.filter(fecha__lte=fin)
        

        total_horas_extra = calcular_horas_extra_por_rango(asistencias)

        

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
