from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("estado-dia/", views.estado_dia, name="estado_dia"),
]
