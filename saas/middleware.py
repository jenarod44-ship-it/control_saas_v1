from .models import Perfil

from .models import Perfil


class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.empresa = None

        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                request.empresa = request.user.perfil_saas.empresa
            except Perfil.DoesNotExist:
                request.empresa = None
            except:
                request.empresa = None

        response = self.get_response(request)
        return response