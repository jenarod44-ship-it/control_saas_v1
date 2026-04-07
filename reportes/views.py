from django.shortcuts import render
from asistencia.models import Asistencia
from nucleo.models import Empleado
from core.services.asistencia_service import calcular_estado_asistencia
from core.services.incidencias import generar_incidencias_por_rango
from core.models import Incidencia
from asistencia.models import Movimiento
from nucleo.models import Empleado
from asistencia.models import TiempoExtra
import csv
from django.http import HttpResponse
from core.utils import calcular_estado_asistencia
from django.shortcuts import render
from django.db.models import Prefetch
from core.utils import calcular_tiempo
from core.decorators import solo_operativo

@solo_operativo
def reporte_asistencia(request):
    from nucleo.models import Empleado
    from core.utils import obtener_empresa_usuario


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

    

    

    from core.utils import calcular_estado_asistencia

    registros = list(registros)  # 🔥 FORZAR evaluación

    from core.utils import calcular_estado_asistencia, calcular_incidencias_asistencia

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
    from core.utils import obtener_empresa_usuario
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
    from core.utils import obtener_empresa_usuario

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # 🔹 BASE
    movimientos = Movimiento.objects.filter(
        tipo__in=["SALIDA_PERMISO", "REGRESO"]
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
        empresa=empresa
    ).select_related("empleado")

    asistencias = Asistencia.objects.filter(
    empresa=empresa
)

    # 🔥 AQUÍ VA
    for asistencia in asistencias:
        asistencia.estado = calcular_estado_asistencia(r.empleado, r.fecha)
    

    if inicio and fin:
        registros = registros.filter(fecha__range=[inicio, fin])
    elif inicio:
        registros = registros.filter(fecha__gte=inicio)
    elif fin:
        registros = registros.filter(fecha__lte=fin)

    if empleado_id and empleado_id != "0":
        asistencias = asistencias.filter(empleado_id=empleado_id)
        
        asistencias = asistencias.order_by("fecha", "empleado__numero_empleado")

    for r in asistencias:
        r.estado = calcular_estado_asistencia(
            r.empleado,
            r.fecha.strftime("%Y-%m-%d"),
        )

    return asistencias
@solo_operativo    
def exportar_tiempos_extra_excel(request):
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    tiempos = TiempoExtra.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    if inicio and fin:
        tiempos = tiempos.filter(fecha__range=[inicio, fin])
    elif inicio:
        tiempos = tiempos.filter(fecha__gte=inicio)
    elif fin:
        tiempos = tiempos.filter(fecha__lte=fin)

    if empleado_id:
        tiempos = tiempos.filter(empleado_id=empleado_id)

    tiempos = tiempos.order_by("empleado__nombre", "fecha")

    # 🔥 EXCEL PRO
    wb = openpyxl.Workbook()
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

    # 🔹 DATOS
    fila = 6
    total_horas = 0

    for t in tiempos:
        horas = t.calcular_horas()
        total_horas += horas

        ws.cell(row=fila, column=1, value=t.empleado.numero_empleado)
        ws.cell(row=fila, column=2, value=t.empleado.nombre)
        ws.cell(row=fila, column=3, value=t.fecha.strftime("%d/%m/%Y"))
        ws.cell(row=fila, column=4, value=t.hora_inicio.strftime("%H:%M") if t.hora_inicio else "")
        ws.cell(row=fila, column=5, value=t.hora_fin.strftime("%H:%M") if t.hora_fin else "")
        ws.cell(row=fila, column=6, value=horas)

        fila += 1

    # 🔹 TOTAL
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
    response["Content-Disposition"] = "attachment; filename=tiempos_extra.xlsx"

    wb.save(response)
    return response



@solo_operativo
def exportar_movimientos_excel(request):
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse

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
    wb = openpyxl.Workbook()
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
    from core.utils import calcular_estado_asistencia, calcular_incidencias_asistencia

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
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse
    from core.utils import calcular_estado_asistencia, calcular_incidencias_asistencia

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    registros = obtener_asistencias_base(request)
    registros = aplicar_filtros_asistencia(request, registros)
    registros = registros.order_by("empleado__numero_empleado", "-fecha")

    wb = openpyxl.Workbook()
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
    

   
def obtener_tiempos_extra(empresa, inicio=None, fin=None, empleado_id=None):

    tiempos = TiempoExtra.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    if inicio and fin:
        tiempos = tiempos.filter(fecha__range=[inicio, fin])

    elif inicio:
        tiempos = tiempos.filter(fecha__gte=inicio)

    elif fin:
        tiempos = tiempos.filter(fecha__lte=fin)

    if empleado_id and empleado_id != "0":
        tiempos = tiempos.filter(empleado_id=empleado_id)

    return tiempos.order_by("fecha", "empleado__numero_empleado")

@solo_operativo
def reporte_tiempos_extra(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # 🔴 SIEMPRE definir primero
    tiempos = TiempoExtra.objects.filter(
        empleado__empresa=empresa
    ).select_related("empleado")

    # 🔹 filtros
    if inicio and fin:
        tiempos = tiempos.filter(fecha__range=[inicio, fin])

    elif inicio:
        tiempos = tiempos.filter(fecha__gte=inicio)

    elif fin:
        tiempos = tiempos.filter(fecha__lte=fin)

    if empleado_id and empleado_id != "":
        tiempos = tiempos.filter(empleado_id=empleado_id)

    # 🔹 orden
    tiempos = tiempos.order_by("empleado__nombre", "fecha")

    # 🔹 total horas
    total_horas = sum([t.calcular_horas() for t in tiempos])

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    context = {
        "tiempos": tiempos,
        "empleados": empleados,
        "inicio": inicio,
        "fin": fin,
        "empleado_id": empleado_id,
        "total_horas": total_horas
    }

    return render(request, "reportes/tiempo_extra.html", context)


from asistencia.models import Movimiento


from django.shortcuts import render

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
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse

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

    wb = openpyxl.Workbook()
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
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse
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
    wb = openpyxl.Workbook()
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