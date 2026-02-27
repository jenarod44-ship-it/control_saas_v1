from django.urls import path
from . import views
app_name = "nucleo"

urlpatterns = [
    path("checador/", views.checador, name="checador"),
    path("reporte-diario/", views.reporte_diario, name="reporte_diario"),
    path("incidencias/", views.incidencias, name="incidencias"),
]



