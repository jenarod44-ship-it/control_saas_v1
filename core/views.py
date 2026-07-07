# Django
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from core.forms import CompanyForm
from core.utils import create_company
from core.forms import CompanyForm
from core.decorators import solo_operativo, solo_admin
from django.shortcuts import redirect


def cambiar_empresa(request, empresa_id):
    request.session['empresa_id'] = empresa_id
    return redirect('dashboard')  # ajusta si tu url es otra


# Python
import csv
from datetime import timedelta, time

# Core
from core.models import Perfil
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

    empresa = request.empresa

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
@login_required
def crear_incidencia(request):

    empresa = getattr(request, "empresa", None)

    if not empresa:
        from core.models import EmpresaUsuario

        relacion = EmpresaUsuario.objects.filter(
            usuario=request.user
        ).select_related("empresa").first()

        if relacion:
            empresa = relacion.empresa

    if not empresa:
        messages.error(request, "No hay empresa activa seleccionada")
        return redirect("core:dashboard")

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

from django.utils import timezone
from django.shortcuts import render



















