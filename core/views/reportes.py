from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render

from core.utils import obtener_empresa_usuario, calcular_estado_asistencia
from nucleo.models import Empleado
from asistencia.models import Asistencia, TiempoExtra
from core.models import IncidenciaDia
from asistencia.models import Movimiento
from datetime import date, datetime
from core.calculadora import CalculadoraAsistencia

@login_required
def estado_dia(request):

    empresa = obtener_empresa_usuario(request.user)

    # 🔥 usar una sola fecha
    fecha_str = request.GET.get("fecha")

    if fecha_str:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha = timezone.localdate()

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    reporte_dia = []

    presentes = 0
    retardos = 0
    faltas = 0

    for empleado in empleados:

        movimientos = Movimiento.objects.filter(
            asistencia__empleado=empleado,
            fecha=fecha
        ).order_by("hora")

        calc = CalculadoraAsistencia(empleado, fecha, movimientos)
        resultado = calc.calcular()

        calc.guardar_incidencias()

        estado = resultado["estado"]

        # 🔢 CONTADORES
        if estado == "RETARDO":
            retardos += 1
        elif estado == "FALTA":
            faltas += 1
        else:
            presentes += 1

        reporte_dia.append({
            "empleado": empleado,
            "entrada": resultado["entrada"],
            "salida": resultado["salida"],
            "horas": resultado["horas_trabajadas"],
            "estado": estado,
            "incidencias": resultado["incidencias"],
        })

    return render(request, "control/estado_dia.html", {
        "reporte_dia": reporte_dia,
        "fecha": fecha,
        "presentes": presentes,
        "retardos": retardos,
        "faltas": faltas
    })




    
