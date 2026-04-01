# Django
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from core.forms import CompanyForm
from core.utils import create_company
from core.forms import CompanyForm


# Python
import csv
from datetime import timedelta, time

# Core
from core.models import Perfil
from core.utils import obtener_empresa_usuario, calcular_estado_asistencia
from core.services.company_service import create_company
from core.services.incidencias import generar_incidencias_por_rango

# Otras apps
from asistencia.models import Asistencia
from nucleo.models import Empleado

# Modelos locales
from .models import Incidencia, IncidenciaDia
from .forms import IncidenciaForm

def create_company_view(request):

    if request.method == "POST":
        form = CompanyForm(request.POST)

        if form.is_valid():
            create_company(request.user, form)
            return redirect("dashboard")

    else:
        form = CompanyForm()

    return render(request, "core/company_form.html", {"form": form})

    

@login_required
def crear_empleado(request):

    empresa = obtener_empresa_usuario(request.user)

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        numero = request.POST.get("numero_empleado")
        departamento_id = request.POST.get("departamento")

        # 🔎 Verificar duplicado
        existe = Empleado.objects.filter(
            empresa=empresa,
            numero_empleado=numero
        ).exists()

        if existe:
            return render(request, "nucleo/crear_empleado.html", {
                "error": "Ese número de empleado ya existe"
            })

        # Crear empleado
        Empleado.objects.create(
            empresa=empresa,
            nombre=nombre,
            numero_empleado=numero,
            departamento_id=departamento_id
        )

        return redirect("core:dashboard")

    return render(request, "control/crear_empleado.html")

    
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


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

from django.utils import timezone
from django.shortcuts import render



















