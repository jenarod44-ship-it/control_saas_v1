from core.utils import obtener_empresa_usuario
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import Perfil
from asistencia.models import Asistencia
from django.http import HttpResponse
import csv
from core.utils import obtener_empresa_usuario
from datetime import timedelta
from .models import IncidenciaDia
from .forms import IncidenciaForm
# imports
from datetime import timedelta
from .models import IncidenciaDia
from .models import Incidencia
from django.apps import apps
Empleado = apps.get_model("nucleo", "Empleado")

def generar_incidencias_por_rango(incidencia):

    fecha = incidencia.fecha_inicio

    while fecha <= incidencia.fecha_fin:

        IncidenciaDia.objects.get_or_create(
            empleado=incidencia.empleado,
            fecha=fecha,
            defaults={
                "tipo": incidencia.tipo,
                "incidencia": incidencia
            }
        )

        fecha += timedelta(days=1)


@login_required
def dashboard(request):
    empresa = obtener_empresa_usuario(request.user)
    hoy = timezone.localdate()

    empleados = Empleado.objects.filter(empresa=empresa, activo=True)

    asistencias_hoy = Asistencia.objects.filter(fecha=hoy, empresa=empresa)

    asistencias_normales = asistencias_hoy.filter(tipo_dia="NORMAL")

    empleados_con_entrada = asistencias_normales.filter(
        hora_entrada__isnull=False
    ).count()

    ausencias_justificadas = asistencias_hoy.exclude(tipo_dia="NORMAL").count()

    empleados_sin_entrada = empleados.count() - empleados_con_entrada - ausencias_justificadas
    asistencias_reales = asistencias_normales.count()

    context = {
        "empresa": empresa,
        "empleados": empleados,   # ⭐ ESTA ES LA CLAVE
        "total_empleados": empleados.count(),
        "asistencias_hoy": asistencias_reales,
        "empleados_sin_entrada": empleados_sin_entrada,
        "ausencias_justificadas": ausencias_justificadas,
    }

    return render(request, "control/dashboard.html", context)


@login_required
def reporte_excel(request):
    perfil = Perfil.objects.get(user=request.user)
    empresa = perfil.empresa
    hoy = timezone.localdate()
    return response

    asistencias_hoy = Asistencia.objects.filter(fecha=hoy)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencia.csv"'

    writer = csv.writer(response)
    writer.writerow(['Empleado', 'Entrada', 'Salida'])

    for asistencia in asistencias_hoy:
        writer.writerow([
            asistencia.empleado.nombre,
            asistencia.hora_entrada,
            asistencia.hora_salida
        ])
@login_required
def crear_empleado(request):

    if request.method == "POST":
        empresa = obtener_empresa_usuario(request.user)

        Empleado.objects.create(
    empresa=empresa,
    nombre=request.POST.get("nombre"),
    numero_empleado=request.POST.get("numero"),
)

        return redirect("dashboard")

    return render(request, "control/crear_empleado.html")

    
from django.contrib import messages

@login_required
def crear_incidencia(request):

    empresa = obtener_empresa_usuario(request.user)

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    if request.method == "POST":

        empleado_id = request.POST.get("empleado")

        empleado = empleados.filter(id=empleado_id).first()

        if not empleado:
            messages.error(request, "Empleado desconocido para tu empresa")
            return redirect("crear_incidencia")

        incidencia = Incidencia.objects.create(
            empleado=empleado,
            tipo=request.POST.get("tipo"),
            fecha_inicio=request.POST.get("fecha_inicio"),
            fecha_fin=request.POST.get("fecha_fin"),
        )

        generar_incidencias_por_rango(incidencia)

        messages.success(request, "Incidencia registrada correctamente")
        return redirect("dashboard")

    return render(
        request,
        "nucleo/incidencias.html",
        {"empleados": empleados}
    )












