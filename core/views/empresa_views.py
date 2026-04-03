from django.shortcuts import redirect, get_object_or_404
from core.models import EmpresaUsuario

def cambiar_empresa(request, empresa_id):
    user = request.user

    relacion = get_object_or_404(
        EmpresaUsuario,
        usuario=user,
        empresa_id=empresa_id,
        activo=True
    )

    request.session["empresa_id"] = relacion.empresa_id

    return redirect("dashboard")