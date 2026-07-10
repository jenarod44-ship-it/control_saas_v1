from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from nucleo.models import Empleado
from asistencia.models import Asistencia, TiempoExtra
from core.models import IncidenciaDia
from core.decorators import solo_operativo
from core.services.asistencia_service import calcular_horas_extra_por_rango
from datetime import datetime, timedelta


@solo_operativo
def dashboard(request):



    empresa = request.empresa
    hoy = timezone.localdate()

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    asistencias = Asistencia.objects.filter(
        empleado__empresa=request.empresa,
        fecha=hoy
    )

    tiempo_extra = calcular_horas_extra_por_rango(asistencias)

    incidencias = IncidenciaDia.objects.filter(
        empleado__empresa=empresa,
        fecha=hoy
    )

    asistencias = Asistencia.objects.filter(
        empleado__empresa=empresa,
        fecha=hoy
    ).select_related("empleado")

    presentes = 0
    retardos = 0
    faltas = 0
    

    empleados_con_incidencia = set(
        IncidenciaDia.objects.filter(
            empleado__empresa=empresa,
            fecha=hoy
        ).values_list("empleado_id", flat=True)
    )

    for empleado in empleados:

        if empleado.id in empleados_con_incidencia:
            continue

        estado = calcular_estado_asistencia(empleado, hoy)

        asistencia = Asistencia.objects.filter(
            empleado=empleado,
            fecha=hoy
        ).first()

        if asistencia and asistencia.hora_entrada and empleado.turno:
            limite_entrada = (
                datetime.combine(hoy, empleado.turno.hora_entrada)
                + timedelta(minutes=empleado.turno.tolerancia_minutos)
            ).time()

            if asistencia.hora_entrada > limite_entrada:
                retardos += 1

        if estado in ["OK", "RETARDO", "INCOMPLETO"]:
            presentes += 1

        elif estado == "FALTA":

            if empleado.turno:
                ahora = timezone.localtime().time()

                limite_entrada = (
                    datetime.combine(hoy, empleado.turno.hora_entrada)
                    + timedelta(minutes=empleado.turno.tolerancia_minutos)
                ).time()

                if ahora <= limite_entrada:
                    continue

            faltas += 1
    from core.models import EmpresaUsuario

    empresas = EmpresaUsuario.objects.filter(
        usuario=request.user
    ).select_related("empresa")

    context = {
        "empresa": empresa,
        "presentes": presentes,
        "retardos": retardos,
        "faltas": faltas,
        "incidencias": incidencias.count(),
        "total_empleados": empleados.count(),
        "tiempo_extra": tiempo_extra
    }

    return render(request, "control/dashboard.html", context)




def home(request):

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    return redirect("login")

from core.utils.asistencia import debe_generar_falta, es_tiempo_extra
from datetime import time


def calcular_estado_asistencia(empleado, fecha):

    

    asistencia = empleado.asistencia_set.filter(fecha=fecha).first()

    dia = fecha.weekday()

    trabaja_fines = (
        empleado.departamento and
        getattr(empleado.departamento, "trabaja_fines_semana", False)
    )

    # 🔥 FIN DE SEMANA
    if dia in [5, 6]:

        if trabaja_fines:
            pass  # flujo normal

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
            return "OK"

    return "RETARDO"

    return "FALTA"

    
    

