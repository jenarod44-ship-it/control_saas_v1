from core.utils.empresa import obtener_empresa_usuario
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import Perfil
from asistencia.models import Asistencia
from django.shortcuts import redirect
from django.apps import apps
Empleado = apps.get_model("nucleo", "Empleado")
from django.apps import apps
from core.views import generar_incidencias_por_rango
from datetime import datetime
from django.contrib import messages
from django.db.models import Q
from asistencia.models import Movimiento
from django.utils import timezone
from asistencia.models import TiempoExtra
from core.models import Incidencia
from django.shortcuts import get_object_or_404, redirect
from .models import Empleado
from .forms import EmpleadoForm
from django.shortcuts import render, redirect
from django.shortcuts import render
from asistencia.models import TiempoExtra
from core.decorators import solo_operativo, solo_admin



def lista_empleados(request):

    empleados = Empleado.objects.all()

    context = {
        "empleados": empleados
    }

    return render(request, "nucleo/lista_empleados.html", context)


def crear_empleado(request):

    if request.method == "POST":
        nombre = request.POST.get("nombre")

        Empleado.objects.create(
            nombre=nombre
        )

        return redirect("nucleo:lista_empleados")

    return render(request, "nucleo/crear_empleado.html")

from django.shortcuts import get_object_or_404

@login_required
def editar_empleado(request, id):
    empleado = get_object_or_404(
        Empleado.objects.for_empresa(request.empresa),
        id=id
    )

    

    if request.method == "POST":
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect("core:dashboard")

    else:
        form = EmpleadoForm(instance=empleado)

    return render(request, "nucleo/editar_empleado.html", {
        "form": form,
        "empleado": empleado
    })

hoy = timezone.localdate()


Empleado = apps.get_model("nucleo", "Empleado")

Incidencia = apps.get_model("core", "Incidencia")

from django.utils import timezone
from django.shortcuts import render
from nucleo.models import Empleado
from asistencia.models import Asistencia, Movimiento



@login_required
def reporte_diario(request):
    empresa = obtener_empresa_usuario(request)

    fecha = request.GET.get("fecha")
    if fecha:
        fecha = timezone.datetime.fromisoformat(fecha).date()
    else:
        fecha = timezone.localdate()

    empleados = Empleado.objects.filter(
        empresa=empresa
    ).order_by("numero_empleado")

    asistencias = Asistencia.objects.filter(
        empresa=empresa,
        fecha=fecha
    )

    mapa = {a.empleado_id: a for a in asistencias}

    filas = []
    for emp in empleados:
        a = mapa.get(emp.id)

        filas.append({
            "empleado": emp,
            "entrada": a.hora_entrada if a else None,
            "salida": a.hora_salida if a else None,
            "tipo": a.tipo_dia if a else None,
            "falta": a is None
        })

        writer.writerow([
            empleado.nombre,
            fecha,
            entrada,
            permiso,
            regreso,
            salida,
            extra_inicio,
            extra_fin,
            estado
        ])

        writer.writerow([
            "Empleado",
            "Fecha",
            "Entrada",
            "Salida permiso",
            "Regreso",
            "Salida",
            "Extra inicio",
            "Extra fin",
            "Estado"
        ])

    return render(request, "nucleo/reporte_diario.html", {
        "filas": filas,
        "fecha": fecha
    })
@login_required
def incidencias(request):

    empresa = obtener_empresa_usuario(request)

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    if request.method == "POST":

        empleado_id = request.POST.get("empleado")
        tipo = request.POST.get("tipo")

        fecha_inicio = datetime.strptime(request.POST.get("fecha_inicio"), "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(request.POST.get("fecha_fin"), "%Y-%m-%d").date()

        empleado = Empleado.objects.get(id=empleado_id, empresa=empresa)

        conflicto = Incidencia.objects.filter(
            empleado=empleado
        ).filter(
            Q(fecha_inicio__lte=fecha_fin) &
            Q(fecha_fin__gte=fecha_inicio)
        ).exists()

        if conflicto:
            messages.warning(request, "Ya existe una incidencia en ese rango para el empleado.")
            return render(request, "nucleo/incidencias.html", {"empleados": empleados})

        incidencia = Incidencia.objects.create(
            empleado=empleado,
            tipo=tipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        generar_incidencias_por_rango(incidencia)

        messages.success(request, "Incidencia registrada correctamente")
        return render(request, "nucleo/incidencias.html", {"empleados": empleados})

    # ✅ ESTE RETURN ES EL QUE TE FALTABA
    return render(request, "nucleo/incidencias.html", {"empleados": empleados})
@login_required
def lista_incidencias(request):

    empresa = obtener_empresa_usuario(request)

    incidencias = Incidencia.objects.filter(
        empleado__empresa=empresa
    ).order_by("-fecha_inicio")

    return render(request, "nucleo/lista_incidencias.html", {
        "incidencias": incidencias
    })
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def crear_incidencia(request):

    empresa = obtener_empresa_usuario(request)

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    if request.method == "POST":

        empleado_id = request.POST.get("empleado")

        empleado = empleados.filter(id=empleado_id).first()

        if not empleado:
            messages.error(request, "Empleado desconocido para tu empresa")
            return redirect("nucleo:crear_incidencia")

        incidencia = Incidencia.objects.create(
            empleado=empleado,
            tipo=request.POST.get("tipo"),
            fecha_inicio=request.POST.get("fecha_inicio"),
            fecha_fin=request.POST.get("fecha_fin"),
        )

        generar_incidencias_por_rango(incidencia)

        messages.success(request, "Incidencia registrada correctamente")
        return redirect("core:dashboard")

    return render(
        request,
        "nucleo/incidencias.html",
        {"empleados": empleados}
    )


      




