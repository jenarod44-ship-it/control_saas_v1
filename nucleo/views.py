from core.utils import obtener_empresa_usuario
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

Empleado = apps.get_model("nucleo", "Empleado")
Incidencia = apps.get_model("core", "Incidencia")

@login_required
def checador(request):
    empresa = obtener_empresa_usuario(request.user)
    mensaje = None

    # ⭐ SIEMPRE disponible
    ultimas = Asistencia.objects.filter(
        empresa=empresa
    ).order_by("-id")[:5]

    if request.method == "POST":

        numero = request.POST.get("numero")

        empleado = Empleado.objects.filter(
            empresa=empresa,
            numero_empleado=numero,
            activo=True
        ).first()

        if not empleado:
            mensaje = "Empleado no encontrado"
            return render(request, "nucleo/checador.html", {
                "mensaje": mensaje,
                "ultimas": ultimas
            })

        hoy = timezone.localdate()

        asistencia, created = Asistencia.objects.get_or_create(
            empresa=empresa,
            empleado=empleado,
            fecha=hoy
        )

        # ⭐ VALIDAR INCIDENCIA
        if asistencia.tipo_dia != "NORMAL":
            mensaje = f"{empleado.nombre} tiene {asistencia.get_tipo_dia_display()} hoy"
            return render(request, "nucleo/checador.html", {
                "mensaje": mensaje,
                "ultimas": ultimas
            })

        if asistencia.hora_entrada is None:
            asistencia.hora_entrada = timezone.localtime().time()
            hora = timezone.localtime().strftime("%H:%M")
            mensaje = f"🟢 Bienvenido {empleado.nombre} — {hora}"

        elif asistencia.hora_salida is None:
            asistencia.hora_salida = timezone.localtime().time()
            hora = timezone.localtime().strftime("%H:%M")
            mensaje = f"🔴 Hasta luego {empleado.nombre} — {hora}"

        else:
            hora = timezone.localtime().strftime("%H:%M")
            mensaje = f"{empleado.nombre}, ya registraste tu jornada hoy — {hora}"

        asistencia.save()

        # ⭐ refrescar lista
        ultimas = Asistencia.objects.filter(
            empresa=empresa
        ).order_by("-id")[:5]

        return render(request, "nucleo/checador.html", {
            "mensaje": mensaje,
            "ultimas": ultimas
        })

    return render(request, "nucleo/checador.html", {
        "mensaje": mensaje,
        "ultimas": ultimas
    })
@login_required
def reporte_diario(request):
    empresa = obtener_empresa_usuario(request.user)

    fecha = request.GET.get("fecha")
    if fecha:
        fecha = timezone.datetime.fromisoformat(fecha).date()
    else:
        fecha = timezone.localdate()

    empleados = Empleado.objects.filter(empresa=empresa, activo=True)

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

    return render(request, "nucleo/reporte_diario.html", {
        "filas": filas,
        "fecha": fecha
    })
@login_required
def incidencias(request):

    empresa = obtener_empresa_usuario(request.user)

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


      




