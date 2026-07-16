from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render

from nucleo.models import Empleado
from asistencia.models import Asistencia, TiempoExtra
from core.models import IncidenciaDia
from asistencia.models import Movimiento
from core.calculadora import CalculadoraAsistencia
from datetime import date, datetime, timedelta

@login_required
def estado_dia(request):

    empresa = request.empresa

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
        extra_inicio = movimientos.filter(tipo="INICIO_TIEMPO_EXTRA").first()
        extra_fin = movimientos.filter(tipo="FIN_TIEMPO_EXTRA").first()

        calc = CalculadoraAsistencia(empleado, fecha, movimientos)
        resultado = calc.calcular()

        # calc.guardar_incidencias()

        estado = resultado["estado"]

        if not empleado.control_horario and estado == "FALTA":
            estado = "SIN CONTROL"

        
        if fecha == timezone.localdate() and estado == "FALTA":

            if empleado.turno:
                ahora = timezone.localtime().time()

                limite_entrada = (
                    datetime.combine(fecha, empleado.turno.hora_entrada)
                    + timedelta(minutes=empleado.turno.tolerancia_minutos)
                ).time()

                if ahora <= limite_entrada:
                    estado = "PENDIENTE"

        # 🔢 CONTADORES
        if estado == "RETARDO":
            presentes += 1
            retardos += 1

        elif estado in ["ASISTENCIA", "OK", "COMPLETO", "INCOMPLETO"]:
            presentes += 1

        elif estado == "FALTA":
            faltas += 1

        reporte_dia.append({
            "empleado": empleado,
            "entrada": resultado["entrada"],
            "salida": resultado["salida"],
            "horas": resultado["horas_trabajadas"],
            "estado": estado,
            "incidencias": resultado["incidencias"],
            "extra_inicio": extra_inicio.hora if extra_inicio else None,
            "extra_fin": extra_fin.hora if extra_fin else None,
        })

    return render(request, "control/estado_dia.html", {
        "reporte_dia": reporte_dia,
        "fecha": fecha,
        "presentes": presentes,
        "retardos": retardos,
        "faltas": faltas
    })




    
