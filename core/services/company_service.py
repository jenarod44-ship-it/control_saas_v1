from core.models import EmpresaUsuario

def create_company(user, form):
    company = form.save(commit=False)
    company.owner = user
    company.save()

    # 🔥 MULTIEMPRESA (sin romper nada)
    EmpresaUsuario.objects.create(
        usuario=user,
        empresa=company
    )

    return company
