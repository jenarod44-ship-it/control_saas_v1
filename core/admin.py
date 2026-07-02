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
    list_display = (
        "id",
        "nombre",
        "razon_social",
        "rfc",
        "subdominio",
        "activa",
        "fecha_alta",
    )

    search_fields = (
        "nombre",
        "razon_social",
        "rfc",
        "subdominio",
    )

    list_filter = (
        "activa",
    )

    ordering = (
        "nombre",
    )

    readonly_fields = (
        "fecha_alta",
    )

    fieldsets = (
        ("Datos generales", {
            "fields": (
                "nombre",
                "razon_social",
                "rfc",
            )
        }),
        ("Configuración SaaS", {
            "fields": (
                "subdominio",
                "activa",
            )
        }),
        ("Auditoría", {
            "fields": (
                "fecha_alta",
            )
        }),
    )

# ========================
# PERFIL
# ========================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "empresa",
    )

    search_fields = (
        "user__username",
        "empresa__nombre",
    )

    list_filter = (
        "empresa",
    )

    ordering = (
        "user__username",
    )

# ========================
# EMPRESA USUARIO
# ========================
@admin.register(EmpresaUsuario)
class EmpresaUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "empresa")
    search_fields = ("usuario__username", "empresa__nombre")
    list_filter = ("empresa",)
    ordering = ("usuario__username",)
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
    list_display = (
        "id",
        "empleado",
        "tipo",
        "turno",
        "fecha_inicio",
        "fecha_fin",
    )

    search_fields = (
        "tipo",
    )

    list_filter = (
        "tipo",
        "fecha_inicio",
    )

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

admin.site.enable_nav_sidebar = False







    