from django.contrib import admin
from .models import Turno, Incidencia, Empresa
from core.models import EmpresaUsuario
from django.contrib import admin
from .models import Perfil, EmpresaUsuario

admin.site.register(Perfil)

admin.site.register(EmpresaUsuario)
admin.site.register(Empresa)

# 🔥 FALTABAN ESTOS
@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'empresa')










    