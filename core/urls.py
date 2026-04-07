from django.urls import path
from . import views
from core.views.empresa import cambiar_empresa

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),  # 👈 ESTA ES LA CLAVE

    path("dashboard/", views.dashboard, name="dashboard"),
    path("estado-dia/", views.estado_dia, name="estado_dia"),

    path(
        "cambiar-empresa/<int:empresa_id>/",
        cambiar_empresa,
        name="cambiar_empresa"
    ),
]
