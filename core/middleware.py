from core.models import Empresa  # ajusta si está en otra app

class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.empresa = None

        if request.user.is_authenticated:

            # 🔥 1. intentar empresa desde sesión
            empresa_id = request.session.get('empresa_id')

            if empresa_id:
                try:
                    request.empresa = Empresa.objects.get(id=empresa_id)
                except Empresa.DoesNotExist:
                    request.empresa = None

            # 🔥 2. fallback (primera empresa del usuario)
            if not request.empresa:
                relacion = request.user.empresausuario_set.first()
                if relacion:
                    request.empresa = relacion.empresa
                    request.session['empresa_id'] = request.empresa.id

        response = self.get_response(request)
        return response
