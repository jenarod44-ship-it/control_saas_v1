class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated and hasattr(request.user, "perfil_core"):
            request.empresa = request.user.perfil_core.empresa
        else:
            request.empresa = None

        return self.get_response(request)
