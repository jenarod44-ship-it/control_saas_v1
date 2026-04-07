from django.contrib import admin
from .models import Turno, Incidencia
from .models import Empresa
from core.models import EmpresaUsuario

admin.site.register(EmpresaUsuario)

admin.site.register(Empresa)











    