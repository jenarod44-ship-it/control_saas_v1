from core.models import Perfil

def obtener_empresa_usuario(user):
    if hasattr(user, "perfil_core") and user.perfil_core.empresa:
        return user.perfil_core.empresa
    return None

    perfil = Perfil.objects.filter(user=user).first()

    if not perfil:
        return None

    return perfil.empresa