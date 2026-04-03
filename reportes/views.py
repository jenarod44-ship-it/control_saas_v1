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
    



def exportar_tiempos_extra_excel(request):

    import csv
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

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_tiempos_extra.csv"'

    writer = csv.writer(response)

    # 🟦 ENCABEZADO EMPRESA
    writer.writerow([f"EMPRESA: {empresa.nombre}"])
    writer.writerow(["REPORTE DE TIEMPOS EXTRA"])
    writer.writerow([])

    # 🟦 FILTROS
    writer.writerow(["FILTROS"])
    writer.writerow(["Fecha inicio:", inicio or ""])
    writer.writerow(["Fecha fin:", fin or ""])
    writer.writerow([])

    # 🟦 ENCABEZADOS TABLA
    writer.writerow([
        "Empleado",
        "Fecha",
        "Hora inicio",
        "Hora fin",
        "Horas"
    ])

    total_horas = 0

    # 🟦 DATOS
    for t in tiempos:

        horas = t.calcular_horas()
        total_horas += horas

        writer.writerow([
            t.empleado.nombre,
            t.fecha,
            t.hora_inicio.strftime("%H:%M") if t.hora_inicio else "",
            t.hora_fin.strftime("%H:%M") if t.hora_fin else "",
            horas
            
        ])


    # 🟦 TOTAL FINAL
    writer.writerow([])
    writer.writerow(["", "", "", "TOTAL GENERAL", total_horas])

    return response



import openpyxl
from django.http import HttpResponse

def exportar_movimientos_excel(request):

    # 1. empresa
    empresa = request.empresa

    # 2. parámetros (UNA sola vez)
    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    # normalizar valores
    if fecha_inicio == "None":
        fecha_inicio = None
    if fecha_fin == "None":
        fecha_fin = None
    if empleado_id == "None":
        empleado_id = None

    # 3. empleado
    empleado = None
    if empleado_id:
        try:
            empleado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            empleado = None

    # 4. queryset (único punto de acceso)
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

    # 📊 Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Movimientos"

    ws.append([
        "No. Empleado",
        "Empleado",
        "Fecha",
        "Hora",
        "Movimiento"
    ])

    for m in movimientos:

        ws.append([
            m.asistencia.empleado.numero_empleado,
            m.asistencia.empleado.nombre,
            m.fecha.strftime("%d/%m/%Y"),   # 👈 FIX
            m.hora.strftime("%H:%M"),       # 👈 FIX
            m.tipo
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=movimientos.xlsx"

    wb.save(response)

    return response
 
def reporte_excel(request):
    import csv
    from django.http import HttpResponse
    from core.utils import calcular_estado_asistencia, calcular_incidencias_asistencia

    registros = obtener_asistencias_base(request)
    registros = aplicar_filtros_asistencia(request, registros)
    registros = registros.order_by("empleado__numero_empleado", "-fecha")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_asistencia.csv"'

    writer = csv.writer(response)

    writer.writerow(["Empleado", "Fecha", "Entrada", "Salida", "Estado", "Incidencias"])

    for r in registros:
        estado = calcular_estado_asistencia(r.empleado, r.fecha)
        incidencias = calcular_incidencias_asistencia(r.empleado, r.fecha)

        writer.writerow([
            r.empleado.nombre,
            r.fecha.strftime("%Y-%m-%d"),
            r.hora_entrada.strftime("%H:%M") if r.hora_entrada else "",
            r.hora_salida.strftime("%H:%M") if r.hora_salida else "",
            estado,
            ", ".join(incidencias) if incidencias else "OK"
        ])

    return response
    

   
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


   
    
def exportar_incidencias_excel(request):


    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")
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
        

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_incidencias.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Empleado",
        "Tipo",
        "Fecha Inicio",
        "Fecha Fin"
    ])

    print(incidencias.count())

    for i in incidencias:

        writer.writerow([
            i.empleado.nombre,
            i.tipo,
            i.fecha_inicio,
            i.fecha_fin
        ])

    return response

def exportar_permisos_excel(request):

    import csv
    from django.http import HttpResponse
    from asistencia.models import Movimiento

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

    # 🔹 ORDEN (igual que web)
    movimientos = movimientos.order_by(
        "asistencia__empleado__numero_empleado",
        "fecha",
        "hora"
    )

    # 🔹 LOGICA (parejas)
    control = {}
    resultados = []

    for m in movimientos:

        key = (m.asistencia_id, m.fecha)

        if m.tipo == "SALIDA_PERMISO":
            control[key] = {
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

    # 🔹 RESPUESTA CSV
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="permisos.csv"'

    writer = csv.writer(response)

    # 🔹 ENCABEZADOS
    writer.writerow([
        "Empleado",
        "Fecha",
        "Salida",
        "Regreso"
    ])

    # 🔹 FILAS
    for r in resultados:
        writer.writerow([
            r["empleado"],
            r["fecha"].strftime("%Y-%m-%d"),
            r["salida"].strftime("%H:%M") if r["salida"] else "",
            r["regreso"].strftime("%H:%M") if r["regreso"] else ""
        ])

    return response