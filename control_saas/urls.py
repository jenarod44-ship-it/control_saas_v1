from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("core.urls")),  # 👈 ESTA se queda

    path("empleados/", include("nucleo.urls")),
    path("asistencia/", include("asistencia.urls")),
    path("movimientos/", include("movimientos.urls")),
    path("reportes/", include(("reportes.urls", "reportes"), namespace="reportes")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("reportes/", include("reportes.urls")),
]











