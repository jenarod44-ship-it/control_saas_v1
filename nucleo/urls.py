from django.urls import path
from . import views

app_name = "nucleo"

urlpatterns = [
    path("crear/", views.crear_empleado, name="crear_empleado"),
    path("lista/", views.lista_empleados, name="lista_empleados"),
    path("<int:empleado_id>/editar/", views.editar_empleado, name="editar_empleado"),
    path("incidencias/", views.lista_incidencias, name="lista_incidencias"),
    path("incidencias/nueva/", views.crear_incidencia, name="crear_incidencia"),
]    




