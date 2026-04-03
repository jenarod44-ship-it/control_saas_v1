from .models import Perfil

from .models import Perfil


class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        pass

        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                pass
            except Perfil.DoesNotExist:
                pass
            except:
                pass

        response = self.get_response(request)
        return response