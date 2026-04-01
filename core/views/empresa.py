from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def cambiar_empresa(request, empresa_id):
    request.session["empresa_id"] = empresa_id
    return redirect("core:dashboard")
