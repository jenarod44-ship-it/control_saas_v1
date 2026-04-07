from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

# 🔐 Solo usuarios logueados
def login_required_view(view_func):
    return login_required(view_func)


# 🔐 Solo admin (superuser)
def solo_admin(view_func):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_superuser:
            return redirect(settings.LOGIN_URL)

        return view_func(request, *args, **kwargs)

    return wrapper


# 🔐 Usuario normal (supervisor)
from django.shortcuts import redirect
from django.conf import settings

def solo_operativo(view_func):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        return view_func(request, *args, **kwargs)

    return wrapper
