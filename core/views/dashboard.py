from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from nucleo.models import Empleado
from asistencia.models import Asistencia, TiempoExtra
from core.models import IncidenciaDia
from core.decorators import solo_operativo
from core.services.asistencia_service import calcular_horas_extra_por_rango



@solo_operativo
def dashboard(request):

    print(dir(request.user))

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
    

    for empleado in empleados:

        estado = calcular_estado_asistencia(empleado, hoy)

        if estado == "OK":
            presentes += 1

        elif estado == "RETARDO":
            presentes += 1
            retardos += 1

        elif estado == "FALTA":
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
            estado = "OK"
        else:
            estado = "RETARDO"

        if not salida:
            estado = "INCOMPLETO"

        return estado

    return "FALTA"

    
    

