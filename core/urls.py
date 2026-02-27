from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("crear-empleado/", views.crear_empleado, name="crear_empleado"),
path("incidencias/nueva/", views.crear_incidencia, name="crear_incidencia"),
]
