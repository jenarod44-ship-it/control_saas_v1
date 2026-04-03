from core.utils import obtener_empresa_usuario


class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            empresa = obtener_empresa_usuario(request)
            print("MIDDLEWARE EMPRESA:", empresa)   # 👈 DEBUG

            request.empresa = empresa
        else:
            request.empresa = None

        return self.get_response(request)
