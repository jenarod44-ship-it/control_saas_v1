from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.utils import timezone

from asistencia.models import Asistencia, Movimiento
from core.calculadora import CalculadoraAsistencia
from core.decorators import solo_operativo
from core.services.asistencia_service import calcular_horas_extra_por_rango
from nucleo.models import Empleado


@solo_operativo
def dashboard(request):

    empresa = request.empresa
    hoy = timezone.localdate()

    empleados = list(
        Empleado.objects.filter(
            empresa=empresa,
            activo=True,
        ).select_related(
            "turno",
            "departamento",
        )
    )

    asistencias = list(
        Asistencia.objects.filter(
            empleado__empresa=empresa,
            fecha=hoy,
        ).select_related("empleado")
    )

    movimientos = list(
        Movimiento.objects.filter(
            asistencia__empleado__empresa=empresa,
            fecha=hoy,
        ).select_related(
            "asistencia",
            "asistencia__empleado",
        ).order_by("hora")
    )

    movimientos_por_empleado = {}

    for movimiento in movimientos:
        empleado_id = movimiento.asistencia.empleado_id

        movimientos_por_empleado.setdefault(
            empleado_id,
            []
        ).append(movimiento)

    presentes = 0
    retardos = 0
    faltas = 0
    incidencias = 0

    for empleado in empleados:

        movimientos_empleado = movimientos_por_empleado.get(
            empleado.id,
            []
        )

        calculadora = CalculadoraAsistencia(
            empleado,
            hoy,
            movimientos_empleado,
        )

        resultado = calculadora.calcular()
        

        estado = resultado["estado"]
        incidencia = resultado.get("incidencia")
        tipo_incidencia = resultado.get("tipo_incidencia", "")

        if incidencia or tipo_incidencia:
            incidencias += 1
            continue

        if estado == "RETARDO":
            presentes += 1
            retardos += 1

        elif estado in [
            "ASISTENCIA",
            "OK",
            "COMPLETO",
            "INCOMPLETO",
        ]:
            presentes += 1

        elif estado == "FALTA":
            faltas += 1

    tiempo_extra = calcular_horas_extra_por_rango(asistencias)

    context = {
        "empresa": empresa,
        "presentes": presentes,
        "retardos": retardos,
        "faltas": faltas,
        "incidencias": incidencias,
        "total_empleados": len(empleados),
        "tiempo_extra": tiempo_extra,
    }

    return render(
        request,
        "control/dashboard.html",
        context,
    )


def home(request):

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    return redirect("login")
    
    

