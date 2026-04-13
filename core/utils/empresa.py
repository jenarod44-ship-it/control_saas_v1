def obtener_empresa_usuario(request):
    user = request.user
    
    # Ajusta según tu modelo real
    if hasattr(user, 'empresa'):
        return user.empresa
    
    return None
