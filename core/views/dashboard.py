from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from core.utils import obtener_empresa_usuario, calcular_estado_asistencia
from nucleo.models import Empleado
from asistencia.models import Asistencia, TiempoExtra
from core.models import IncidenciaDia


@login_required
def dashboard(request):

    empresa = request.empresa
    hoy = timezone.localdate()

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    asistencias = Asistencia.objects.filter(
        empresa=empresa,
        fecha=hoy
    ).select_related("empleado")

    incidencias = IncidenciaDia.objects.filter(
        empleado__empresa=empresa,
        fecha=hoy
    )

    tiempos_extra = TiempoExtra.objects.filter(
        asistencia__empresa=empresa,
        fecha=hoy
    )

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
        "tiempo_extra": tiempos_extra.count(),
        "total_empleados": empleados.count(),
    }

    return render(request, "control/dashboard.html", context)


def home(request):

    if request.user.is_authenticated:
        return redirect("core:dashboard")

    return redirect("login")
    
    

