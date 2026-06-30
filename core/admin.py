from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Turno, Incidencia, Empresa, Perfil
from core.models import EmpresaUsuario


# ========================
# EMPRESA
# ========================
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


# ========================
# PERFIL
# ========================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "empresa")
    search_fields = ("user__username",)
    list_filter = ("empresa",)


# ========================
# EMPRESA USUARIO
# ========================
@admin.register(EmpresaUsuario)
class EmpresaUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "empresa")
    search_fields = ("user__username",)
    list_filter = ("empresa",)


# ========================
# TURNO
# ========================
@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "empresa")
    search_fields = ("nombre",)
    list_filter = ("empresa",)


# ========================
# INCIDENCIA
# ========================
@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "empresa")
    search_fields = ("nombre",)
    list_filter = ("empresa",)


# ========================
# USER + PERFIL INLINE
# ========================
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)







    