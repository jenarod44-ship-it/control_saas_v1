from django.shortcuts import render
from asistencia.models import Asistencia
from nucleo.models import Empleado
from core.services.asistencia_service import calcular_estado_asistencia
from core.services.incidencias import generar_incidencias_por_rango
from core.models import Incidencia
from asistencia.models import Movimiento
from nucleo.models import Empleado
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Prefetch
from core.decorators import solo_operativo
from core.utils.asistencia import debe_generar_falta
from core.utils.laboral import es_dia_laboral
from core.utils.asistencia import debe_generar_falta, es_tiempo_extra
from datetime import time
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from django.http import HttpResponse
from openpyxl.styles import Alignment


def calcular_estado_asistencia(empleado, fecha):

    print("DEPTO:", empleado.departamento)
    print("TRABAJA FINES:", getattr(empleado.departamento, "trabaja_fines_semana", "NO EXISTE"))

    asistencia = empleado.asistencia_set.filter(fecha=fecha).first()

    dia = fecha.weekday()

    trabaja_fines = (
        empleado.departamento and
        getattr(empleado.departamento, "trabaja_fines_semana", False)
    )

    # 🔥 obtener asistencia
    asistencia = empleado.asistencia_set.filter(fecha=fecha).first()

    # 🔥 SI ES FIN DE SEMANA
    if dia in [5, 6]:

        # 🟢 SEGURIDAD → flujo normal
        if trabaja_fines:
            pass

        # 🔵 OTROS EMPLEADOS
        else:
            if asistencia:
                return "TIEMPO_EXTRA"

            return "NO_LABORAL"
    
    if not asistencia:
        return "FALTA"

    entrada = asistencia.hora_entrada
    salida = asistencia.hora_salida

    if es_tiempo_extra(empleado, fecha):
        return "TIEMPO_EXTRA"

    hora_limite_retardo = time(8, 15)

    if entrada:

        if entrada <= hora_limite_retardo:
            estado = "OK"
        else:
            estado = "RETARDO"

        if not salida:
            estado = "INCOMPLETO"

        return estado

    return "FALTA"

from datetime import datetime

def calcular_tiempo(salida, regreso):

    if not salida or not regreso:
        return ""

    t_salida = datetime.combine(datetime.today(), salida)
    t_regreso = datetime.combine(datetime.today(), regreso)

    diferencia = t_regreso - t_salida

    horas = diferencia.seconds // 3600
    minutos = (diferencia.seconds % 3600) // 60

    return f"{horas:02d}:{minutos:02d}"

from core.utils.asistencia import debe_generar_falta, es_tiempo_extra
from datetime import time


def calcular_estado_asistencia(empleado, fecha):

    if not debe_generar_falta(empleado, fecha):
        return "NO_LABORAL"

    asistencia = empleado.asistencia_set.filter(fecha=fecha).first()

    if not asistencia:
        return "FALTA"

    entrada = asistencia.hora_entrada
    salida = asistencia.hora_salida

    if es_tiempo_extra(empleado, fecha):
        return "TIEMPO_EXTRA"

    hora_limite_retardo = time(8, 15)

    if entrada:

        if entrada <= hora_limite_retardo:
            estado = "OK"
        else:
            estado = "RETARDO"

        if not salida:
            estado = "INCOMPLETO"

        return estado

    return "FALTA"

def calcular_incidencias_asistencia(empleado, fecha):

    incidencias = []

    incidencias_qs = Incidencia.objects.filter(
        empleado=empleado,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha
    )

    for i in incidencias_qs:
        incidencias.append(i.tipo if hasattr(i, "tipo") else "INCIDENCIA")

    return incidencias

@solo_operativo
def reporte_asistencia(request):
    from nucleo.models import Empleado
    


    empresa = request.empresa

    print("EMPRESA ACTUAL:", request.empresa)


    registros = obtener_asistencias_base(request)

    
    print("TOTAL REGISTROS:", registros.count())
    registros = aplicar_filtros_asistencia(request, registros)
    registros = registros.order_by("empleado__numero_empleado", "-fecha")

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    

    registros = list(registros)  # 🔥 FORZAR evaluación


    for r in registros:
        r.estado = calcular_estado_asistencia(r.empleado, r.fecha)
        r.incidencias = calcular_incidencias_asistencia(r.empleado, r.fecha) 
         
       
    return render(request, "reportes/asistencia.html", {
        "resultados": registros,
        "empleados": empleados,
        "inicio": request.GET.get("inicio"),
        "fin": request.GET.get("fin"),
        "empleado_id": request.GET.get("empleado"),
    })




def obtener_asistencias_base(request):
    from asistencia.models import Asistencia

    empresa = request.empresa

    return Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

def aplicar_filtros_asistencia(request, queryset):
    empleado_id = request.GET.get("empleado")
    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    if empleado_id and empleado_id not in ["", "0"]:
        queryset = queryset.filter(empleado_id=empleado_id)

    if inicio:
        queryset = queryset.filter(fecha__gte=inicio)

    if fin:
        queryset = queryset.filter(fecha__lte=fin)

    return queryset



def obtener_movimientos(empresa, fecha_inicio=None, fecha_fin=None, empleado=None):

    qs = Movimiento.objects.filter(asistencia__empresa=empresa)

    # 🔹 usar asistencia__fecha (CORRECTO)
    if fecha_inicio and fecha_fin and fecha_inicio == fecha_fin:
        qs = qs.filter(asistencia__fecha=fecha_inicio)
    else:
        if fecha_inicio:
            qs = qs.filter(asistencia__fecha__gte=fecha_inicio)
        if fecha_fin:
            qs = qs.filter(asistencia__fecha__lte=fecha_fin)

    # 🔹 empleado
    if empleado:
        qs = qs.filter(asistencia__empleado=empleado)

    return qs.select_related("asistencia", "asistencia__empleado").order_by("hora")

@solo_operativo
def reporte_permisos(request):

    from asistencia.models import Movimiento
    from nucleo.models import Empleado

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # 🔹 BASE
    movimientos = Movimiento.objects.filter(
        tipo__in=["SALIDA_PERMISO", "REGRESO"],
        asistencia__empleado__empresa=request.empresa  # 🔥 CLAVE
    ).select_related("asistencia__empleado")

    # 🔹 FILTROS
    if inicio:
        movimientos = movimientos.filter(fecha__gte=inicio)
    if fin:
        movimientos = movimientos.filter(fecha__lte=fin)
    if empleado_id:
        movimientos = movimientos.filter(
            asistencia__empleado_id=empleado_id
        )

    # 🔹 ORDEN
    movimientos = movimientos.order_by(
        "asistencia__empleado__numero_empleado",
        "fecha",
        "hora"
    )

    # 🔹 LOGICA (igual que excel)
    control = {}
    resultados = []

    for m in movimientos:

        key = (m.asistencia_id, m.fecha)

        if m.tipo == "SALIDA_PERMISO":
            control[key] = {
                "numero_empleado": m.asistencia.empleado.numero_empleado,
                "empleado": m.asistencia.empleado.nombre,
                "fecha": m.fecha,
                "salida": m.hora,
                "regreso": None
            }

        elif m.tipo == "REGRESO" and key in control:

            data = control[key]
            data["regreso"] = m.hora

            resultados.append(data)

            del control[key]

    # 🔹 EMPLEADOS (filtro)
    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    return render(request, "reportes/permisos.html", {
        "resultados": resultados,   # 🔥 CLAVE
        "empleados": empleados,
        "empleado_id": empleado_id,
        "inicio": inicio,
        "fin": fin
    })
    
def obtener_asistencias(empresa, inicio=None, fin=None, empleado_id=None):

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    # 🔹 filtros opcionales
    if inicio:
        asistencias = asistencias.filter(fecha__gte=inicio)

    if fin:
        asistencias = asistencias.filter(fecha__lte=fin)

    if empleado_id:
        asistencias = asistencias.filter(empleado_id=empleado_id)

    # 🔥 calcular estado
    for asistencia in asistencias:
        asistencia.estado = calcular_estado_asistencia(
            asistencia.empleado,
            asistencia.fecha
        )

    return asistencias

@solo_operativo    
def exportar_tiempos_extra_excel(request):
    

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    # 🔥 FILTRO POR FECHA
    if inicio and fin:
        asistencias = asistencias.filter(fecha__range=(inicio, fin))
    elif inicio:
        asistencias = asistencias.filter(fecha__gte=inicio)
    elif fin:
        asistencias = asistencias.filter(fecha__lte=fin)

# 🔥 FILTRO POR EMPLEADO
    if empleado_id and empleado_id != "0":
        asistencias = asistencias.filter(empleado_id=empleado_id)

    # 🔥 ORDEN
    asistencias = asistencias.order_by("empleado__nombre", "fecha")

        # 🔥 EXCEL PRO
    wb = Workbook()
    ws = wb.active
    ws.title = "Tiempos Extra"

    # 🔹 TITULO
    ws["A1"] = "REPORTE DE TIEMPOS EXTRA"
    ws["A1"].font = Font(bold=True, size=14)

    # 🔹 EMPRESA
    ws["A2"] = f"Empresa: {empresa.nombre if empresa else ''}"

    # 🔹 PERIODO
    if inicio and fin:
        ws["A3"] = f"Periodo: {inicio} a {fin}"
    elif inicio:
        ws["A3"] = f"Desde: {inicio}"
    elif fin:
        ws["A3"] = f"Hasta: {fin}"
    else:
        ws["A3"] = "Periodo: Todos"

    # 🔹 ENCABEZADOS
    encabezados = [
        "No. Empleado",
        "Empleado",
        "Fecha",
        "Hora inicio",
        "Hora fin",
        "Horas"
    ]

    for col, valor in enumerate(encabezados, 1):
        ws.cell(row=5, column=col, value=valor)

    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    from core.services.asistencia_service import obtener_tiempo_extra

    # 🔹 DATOS
    fila = 6
    total_horas = 0

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    for a in asistencias:

        info = obtener_tiempo_extra(a)

        if info:

            ws.cell(row=fila, column=1, value=a.empleado.numero_empleado)
            ws.cell(row=fila, column=2, value=a.empleado.nombre)
            ws.cell(row=fila, column=3, value=a.fecha)
            ws.cell(row=fila, column=4, value=info["inicio"])
            ws.cell(row=fila, column=5, value=info["fin"])
            ws.cell(row=fila, column=6, value=info["horas"])

            # 🔥 sumar solo si es número
            if isinstance(info["horas"], int):
                total_horas += info["horas"]

            fila += 1


    # 🔹 TOTAL (FUERA DEL FOR)
    ws.cell(row=fila + 1, column=5, value="TOTAL GENERAL").font = Font(bold=True)
    ws.cell(row=fila + 1, column=6, value=total_horas).font = Font(bold=True)


# 🔹 AUTO ANCHO
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2


    # 🔹 FREEZE
    ws.freeze_panes = "A6"


    # 🔹 BORDES
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            cell.border = Border(
                top=thin,
                left=thin,
                right=thin,
                bottom=thin
            )


    # 🔹 RESPONSE (FUERA DE TODO)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=tiempos_extra.xlsx"

    wb.save(response)
    return response


@solo_operativo
def exportar_movimientos_excel(request):
    

    # 🔹 empresa
    empresa = request.empresa

    # 🔹 parámetros
    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    if fecha_inicio == "None":
        fecha_inicio = None
    if fecha_fin == "None":
        fecha_fin = None
    if empleado_id == "None":
        empleado_id = None

    # 🔹 empleado
    empleado = None
    if empleado_id:
        try:
            empleado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            empleado = None

    # 🔹 queryset (NO tocar)
    movimientos = obtener_movimientos(
        empresa=empresa,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        empleado=empleado
    )

    if empleado_id:
        movimientos = movimientos.filter(
            asistencia__empleado_id=int(empleado_id)
        )

    movimientos = movimientos.order_by("fecha", "hora")

    # 🔥 EXCEL PRO
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"

    # 🔹 TITULO
    ws["A1"] = "REPORTE DE MOVIMIENTOS"
    ws["A1"].font = Font(bold=True, size=14)

    # 🔹 EMPRESA
    ws["A2"] = f"Empresa: {empresa.nombre if empresa else ''}"

    # 🔹 PERIODO
    if fecha_inicio and fecha_fin:
        ws["A3"] = f"Periodo: {fecha_inicio} a {fecha_fin}"
    elif fecha_inicio:
        ws["A3"] = f"Desde: {fecha_inicio}"
    elif fecha_fin:
        ws["A3"] = f"Hasta: {fecha_fin}"
    else:
        ws["A3"] = "Periodo: Todos"

    # 🔹 ENCABEZADOS (fila 5)
    encabezados = [
        "No. Empleado",
        "Empleado",
        "Fecha",
        "Hora",
        "Movimiento"
    ]

    for col, valor in enumerate(encabezados, 1):
        ws.cell(row=5, column=col, value=valor)

    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 🔹 DATOS (desde fila 6)
    fila = 6

    for m in movimientos:
        ws.cell(row=fila, column=1, value=m.asistencia.empleado.numero_empleado)
        ws.cell(row=fila, column=2, value=m.asistencia.empleado.nombre)
        ws.cell(row=fila, column=3, value=m.fecha.strftime("%d/%m/%Y"))
        ws.cell(row=fila, column=4, value=m.hora.strftime("%H:%M"))
        ws.cell(row=fila, column=5, value=m.tipo)
        fila += 1

    # 🔹 AUTO ANCHO
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2

    # 🔹 FREEZE
    ws.freeze_panes = "A6"

    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            cell.border = Border(
                top=thin,
                left=thin,
                right=thin,
                bottom=thin
            )

    # 🔹 RESPONSE
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=movimientos.xlsx"

    wb.save(response)
    return response

  
 
def reporte_excel(request):
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    

    registros = obtener_asistencias_base(request)
    registros = aplicar_filtros_asistencia(request, registros)
    registros = registros.order_by("empleado__numero_empleado", "-fecha")

    response = HttpResponse(content_type="text/csv")

    # ✅ nombre dinámico
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    import uuid

    response["Content-Disposition"] = f'attachment; filename="asistencia_{uuid.uuid4().hex}.csv"'

    writer = csv.writer(response)

    # ✅ encabezados claros
    writer.writerow([
        "Empleado",
        "Fecha",
        "Hora Entrada",
        "Hora Salida",
        "Estado",
        "Incidencias"
    ])

    for r in registros:
        estado = calcular_estado_asistencia(r.empleado, r.fecha)
        incidencias = calcular_incidencias_asistencia(r.empleado, r.fecha)

        writer.writerow([
            r.empleado.nombre,
            r.fecha.strftime("%d/%m/%Y"),
            r.hora_entrada.strftime("%H:%M") if r.hora_entrada else "--",
            r.hora_salida.strftime("%H:%M") if r.hora_salida else "--",
            estado,
            " | ".join(incidencias) if incidencias else "OK"
        ])
    return response

@solo_operativo
def reporte_excel_xlsx(request):

    from openpyxl.styles import Alignment  # 🔥 FORZAR CONTEXTO
    
    

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    registros = obtener_asistencias_base(request)
    registros = aplicar_filtros_asistencia(request, registros)
    registros = registros.order_by("empleado__numero_empleado", "-fecha")

    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    # 🔹 TITULO
    ws["A1"] = "REPORTE DE ASISTENCIA"
    ws["A1"].font = Font(bold=True, size=14)

    ws["A2"] = f"Empresa: {empresa.nombre if empresa else ''}"

    if inicio and fin:
        ws["A3"] = f"Periodo: {inicio} a {fin}"
    elif inicio:
        ws["A3"] = f"Desde: {inicio}"
    elif fin:
        ws["A3"] = f"Hasta: {fin}"
    else:
        ws["A3"] = "Periodo: Todos"

    # 👉 encabezados SIEMPRE en fila 5
    fila_encabezado = 5
    
    # 🔹 ENCABEZADOS
    encabezados = [
        "No. Empleado",
        "Empleado",
        "Fecha",
        "Hora Entrada",
        "Hora Salida",
        "Estado",
        "Incidencias"
    ]

    for col, valor in enumerate(encabezados, 1):
         ws.cell(row=5, column=col, value=valor)

    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 🔹 CONGELAR
    ws.freeze_panes = "A6"

    

    # 🔹 NEGRITAS EN ENCABEZADOS
    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 🔹 DATOS
    fila = 6

    for r in registros:
        estado = calcular_estado_asistencia(r.empleado, r.fecha)
        incidencias = calcular_incidencias_asistencia(r.empleado, r.fecha)

        ws.cell(row=fila, column=1, value=r.empleado.numero_empleado)
        ws.cell(row=fila, column=2, value=r.empleado.nombre)
        ws.cell(row=fila, column=3, value=r.fecha.strftime("%d/%m/%Y"))
        ws.cell(row=fila, column=4, value=r.hora_entrada.strftime("%H:%M") if r.hora_entrada else "--")
        ws.cell(row=fila, column=5, value=r.hora_salida.strftime("%H:%M") if r.hora_salida else "--")
        ws.cell(row=fila, column=6, value=estado)
        ws.cell(row=fila, column=7, value=" | ".join(incidencias) if incidencias else "OK")

        fila += 1   
        

    from openpyxl.styles import PatternFill
    verde = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    rojo = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    amarillo = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    gris = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

    for row in ws.iter_rows(min_row=6, max_row=ws.max_row):
        incidencia_cell = row[5]  # 👈 columna Incidencias

        if not incidencia_cell.value:
            continue

        texto = str(incidencia_cell.value).strip().upper()

        if texto == "OK":
            incidencia_cell.fill = verde
        elif "SIN SALIDA" in texto:
            incidencia_cell.fill = rojo
        elif "RETARDO" in texto:
            incidencia_cell.fill = amarillo
        elif "SIN TURNO" in texto:
            incidencia_cell.fill = gris

    from openpyxl.styles import Alignment

    for row in ws.iter_rows(min_row=6):
        row[2].alignment = Alignment(horizontal="center")  # Hora Entrada
        row[3].alignment = Alignment(horizontal="center")  # Hora Salida
        row[4].alignment = Alignment(horizontal="center")  # Estado

    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=7):
        for cell in row:
            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

    # 🔹 AJUSTE AUTOMÁTICO DE COLUMNAS
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[column_letter].width = max_length + 2

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=asistencia.xlsx"

    wb.save(response)
    return(response)
    

   
@solo_operativo
def reporte_tiempos_extra(request):
    

    from asistencia.models import Asistencia, Movimiento
    from nucleo.models import Empleado
    from datetime import datetime
    from asistencia.models import Movimiento

    print("TOTAL MOVIMIENTOS:", Movimiento.objects.count())

    for m in Movimiento.objects.all()[:10]:
        print("MOV:", m.id, m.tipo, m.hora, m.asistencia_id)

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    # 🔹 filtros
    if inicio and fin:
        asistencias = asistencias.filter(fecha__range=[inicio, fin])
    elif inicio:
        asistencias = asistencias.filter(fecha__gte=inicio)
    elif fin:
        asistencias = asistencias.filter(fecha__lte=fin)

    if empleado_id and empleado_id != "":
        asistencias = asistencias.filter(empleado_id=empleado_id)

    asistencias = asistencias.order_by("empleado__nombre", "fecha")

    resultados = []
    total_horas = 0

    for a in asistencias:

        movimientos = Movimiento.objects.filter(
            asistencia__empleado=a.empleado,
            asistencia__fecha=a.fecha
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
                # 🔥 calcular minutos totales
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

                total_horas += horas_final

                resultados.append({
                    "empleado": a.empleado,
                    "fecha": a.fecha,
                    "hora_inicio": inicio_extra,
                    "hora_fin": fin_extra,
                    "horas": horas_final   # 🔥 SOLO ENTERO
                })

            else:
                # 🔥 EN CURSO
                resultados.append({
                    "empleado": a.empleado,
                    "fecha": a.fecha,
                    "hora_inicio": inicio_extra,
                    "hora_fin": None,
                    "horas": "EN CURSO"
                })
                
    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    context = {
        "tiempos": resultados,
        "empleados": empleados,
        "inicio": inicio,
        "fin": fin,
        "empleado_id": empleado_id,
        "total_horas": round(total_horas, 2)
    }

    return render(request, "reportes/tiempo_extra.html", context)

@solo_operativo
def reporte_movimientos(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # 🔥 limpiar valores
    if inicio == "None":
        inicio = None
    if fin == "None":
        fin = None
    if empleado_id == "None":
        empleado_id = None

    movimientos = Movimiento.objects.select_related(
        "asistencia__empleado"
    ).filter(
        asistencia__empleado__empresa=empresa
    )

    # 🔥 FILTROS
    if inicio and fin:
        movimientos = movimientos.filter(fecha__range=[inicio, fin])
    elif inicio:
        movimientos = movimientos.filter(fecha__gte=inicio)
    elif fin:
        movimientos = movimientos.filter(fecha__lte=fin)

    if empleado_id:
        movimientos = movimientos.filter(
            asistencia__empleado_id=int(empleado_id)
        )

    movimientos = movimientos.order_by(
        "asistencia__empleado", "fecha", "hora"
    )

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    return render(request, "reportes/movimientos.html", {
        "movimientos": movimientos,
        "empleados": empleados,
        "empleado_id": empleado_id,
        "inicio": inicio,
        "fin": fin
    })

    
@solo_operativo
def reporte_incidencias(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # ✅ PRIMERO crear queryset base
    incidencias = Incidencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    # ✅ luego aplicar filtros
    if inicio and fin:
        incidencias = incidencias.filter(fecha_inicio__range=[inicio, fin])

    elif inicio:
        incidencias = incidencias.filter(fecha_inicio__gte=inicio)

    elif fin:
        incidencias = incidencias.filter(fecha_inicio__lte=fin)

    if empleado_id and empleado_id != "0":
        incidencias = incidencias.filter(empleado_id=empleado_id)

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )
    context = {
        "incidencias": incidencias,
        "empleados": empleados,
        "inicio": inicio,
        "fin": fin,
        "empleado_id": empleado_id
    }

    return render(request, "reportes/incidencias.html", context)

    



def index(request):
    return render(request, "reportes/index.html")


   
@solo_operativo    
def exportar_incidencias_excel_xlsx(request):
    

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    incidencias = Incidencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    if empleado_id and empleado_id != "":
        incidencias = incidencias.filter(empleado_id=empleado_id)

    if inicio and fin:
        incidencias = incidencias.filter(
            fecha_inicio__range=[inicio, fin]
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "Incidencias"

    # 🔹 TITULO
    ws["A1"] = "REPORTE DE INCIDENCIAS"
    ws["A1"].font = Font(bold=True, size=14)

    # 🔹 EMPRESA
    ws["A2"] = f"Empresa: {empresa.nombre if empresa else ''}"

    # 🔹 PERIODO
    if inicio and fin:
        ws["A3"] = f"Periodo: {inicio} a {fin}"
    elif inicio:
        ws["A3"] = f"Desde: {inicio}"
    elif fin:
        ws["A3"] = f"Hasta: {fin}"
    else:
        ws["A3"] = "Periodo: Todos"

    # 🔹 ENCABEZADOS
    encabezados = [
        "No. Empleado",
        "Empleado",
        "Tipo",
        "Fecha Inicio",
        "Fecha Fin"
    ]

    for col, valor in enumerate(encabezados, 1):
        ws.cell(row=5, column=col, value=valor)

    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 🔹 DATOS
    fila = 6

    for i in incidencias:
        ws.cell(row=fila, column=1, value=i.empleado.numero_empleado)
        ws.cell(row=fila, column=2, value=i.empleado.nombre)
        ws.cell(row=fila, column=3, value=i.tipo)
        ws.cell(row=fila, column=4, value=i.fecha_inicio.strftime("%d/%m/%Y") if i.fecha_inicio else "")
        ws.cell(row=fila, column=5, value=i.fecha_fin.strftime("%d/%m/%Y") if i.fecha_fin else "")
        fila += 1

    # 🔹 AJUSTE COLUMNAS
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2

    # 🔹 FREEZE
    ws.freeze_panes = "A6"

    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            cell.border = Border(
                top=thin,
                left=thin,
                right=thin,
                bottom=thin
            )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=incidencias.xlsx"

    wb.save(response)
    return response

@solo_operativo
def exportar_permisos_excel(request):
    
    from asistencia.models import Movimiento

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # 🔹 BASE
    movimientos = Movimiento.objects.filter(
        tipo__in=["SALIDA_PERMISO", "REGRESO"],
        asistencia__empleado__empresa=empresa
    ).select_related("asistencia__empleado")

    # 🔹 FILTROS
    if inicio:
        movimientos = movimientos.filter(fecha__gte=inicio)
    if fin:
        movimientos = movimientos.filter(fecha__lte=fin)
    if empleado_id:
        movimientos = movimientos.filter(
            asistencia__empleado_id=empleado_id
        )

    # 🔹 ORDEN
    movimientos = movimientos.order_by(
        "asistencia__empleado__numero_empleado",
        "fecha",
        "hora"
    )

    # 🔹 LOGICA (NO TOCAR)
    control = {}
    resultados = []

    for m in movimientos:

        key = (m.asistencia_id, m.fecha)

        if m.tipo == "SALIDA_PERMISO":
            control[key] = {
            "numero_empleado": m.asistencia.empleado.numero_empleado,
            "empleado": m.asistencia.empleado.nombre,
            "fecha": m.fecha,
            "salida": m.hora,
            "regreso": None
        }

        elif m.tipo == "REGRESO" and key in control:

            data = control[key]
            data["regreso"] = m.hora

            resultados.append(data)

            del control[key]

    # 🔥 EXCEL PRO
    wb = Workbook()
    ws = wb.active
    ws.title = "Permisos"

    # 🔹 TITULO
    ws["A1"] = "REPORTE DE PERMISOS"
    ws["A1"].font = Font(bold=True, size=14)

    # 🔹 EMPRESA
    ws["A2"] = f"Empresa: {empresa.nombre if empresa else ''}"

    # 🔹 PERIODO
    if inicio and fin:
        ws["A3"] = f"Periodo: {inicio} a {fin}"
    elif inicio:
        ws["A3"] = f"Desde: {inicio}"
    elif fin:
        ws["A3"] = f"Hasta: {fin}"
    else:
        ws["A3"] = "Periodo: Todos"

    # 🔹 ENCABEZADOS
    encabezados = [
        "No. Empleado",
        "Empleado",
        "Fecha",
        "Salida",
        "Regreso"
    ]

    for col, valor in enumerate(encabezados, 1):
        ws.cell(row=5, column=col, value=valor)

    for cell in ws[5]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # 🔹 DATOS
    fila = 6

    for r in resultados:
        ws.cell(row=fila, column=1, value=r["numero_empleado"])
        ws.cell(row=fila, column=2, value=r["empleado"])
        ws.cell(row=fila, column=3, value=r["fecha"].strftime("%d/%m/%Y"))
        ws.cell(row=fila, column=4, value=r["salida"].strftime("%H:%M") if r["salida"] else "")
        ws.cell(row=fila, column=5, value=r["regreso"].strftime("%H:%M") if r["regreso"] else "")
        fila += 1

    # 🔹 AUTO ANCHO
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2

    # 🔹 FREEZE
    ws.freeze_panes = "A6"

    from openpyxl.styles import Border, Side

    thin = Side(style="thin")

    for row in ws.iter_rows(min_row=5, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            cell.border = Border(
                top=thin,
                left=thin,
                right=thin,
                bottom=thin
            )
    

    # 🔹 RESPONSE
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=permisos.xlsx"

    wb.save(response)
    return response

from core.services.asistencia_service import obtener_tiempo_extra

def reporte_nomina(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    if inicio and fin:
        asistencias = asistencias.filter(fecha__range=(inicio, fin))
    elif inicio:
        asistencias = asistencias.filter(fecha__gte=inicio)
    elif fin:
        asistencias = asistencias.filter(fecha__lte=fin)

    empleados = {}
    total_general = 0  # 🔥 SIEMPRE DEFINIDO

    for a in asistencias:
        emp = a.empleado

        if emp.id not in empleados:
            empleados[emp.id] = {
                "empleado": emp,
                "horas": 0,
                "pago": 0
            }

        info = obtener_tiempo_extra(a)  # 🔥 ESTA LÍNEA FALTABA

        horas = 0

        if info:
            horas = float(info.get("horas", 0))

        pago = horas * float(emp.costo_hora or 0) * 2

        empleados[emp.id]["horas"] += horas
        empleados[emp.id]["pago"] += pago
        
        

    # 🔥 SIEMPRE SE EJECUTA (aunque no haya datos)
    total_general = sum(e["pago"] for e in empleados.values()) if empleados else 0
    context = {
        "empleados": empleados.values(),
        "inicio": inicio,
        "fin": fin,
        "total_general": total_general
}
    return render(request, "reportes/nomina.html", context)

    from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from core.services.asistencia_service import obtener_tiempo_extra


def exportar_nomina_excel(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    if inicio and fin:
        asistencias = asistencias.filter(fecha__range=(inicio, fin))

    empleados = {}

    for a in asistencias:
        emp = a.empleado

        if emp.id not in empleados:
            empleados[emp.id] = {
                "empleado": emp,
                "horas": 0,
                "pago": 0
            }

        info = obtener_tiempo_extra(a)

        if info and isinstance(info["horas"], int):
            horas = info["horas"]
            pago = horas * float(emp.costo_hora) * 2

            empleados[emp.id]["horas"] += horas
            empleados[emp.id]["pago"] += pago

    # 🔥 CREAR EXCEL
    wb = Workbook()
    ws = wb.active
    ws.title = "Nómina"

    # 🔹 ENCABEZADOS
    encabezados = ["No. Empleado", "Empleado", "Horas", "Costo Hora", "Pago"]

    for col, valor in enumerate(encabezados, 1):
        cell = ws.cell(row=1, column=col, value=valor)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    fila = 2
    total_general = 0

    for e in empleados.values():

        if e["horas"] > 0:

            ws.cell(row=fila, column=1, value=e["empleado"].numero_empleado)
            ws.cell(row=fila, column=2, value=e["empleado"].nombre)
            ws.cell(row=fila, column=3, value=e["horas"])
            ws.cell(row=fila, column=4, value=float(e["empleado"].costo_hora))
            ws.cell(row=fila, column=5, value=e["pago"])

            total_general += e["pago"]
            fila += 1

    # 🔹 TOTAL
    ws.cell(row=fila + 1, column=4, value="TOTAL").font = Font(bold=True)
    ws.cell(row=fila + 1, column=5, value=total_general).font = Font(bold=True)

    # 🔹 AUTO AJUSTE
    for column in ws.columns:
        max_length = 0
        col_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2

    # 🔹 RESPONSE
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=nomina.xlsx"

    wb.save(response)
    return response