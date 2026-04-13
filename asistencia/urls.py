from django.urls import path
from . import views

app_name = "asistencia"

urlpatterns = [
    path("checador/", views.checador, name="checador"),
    path("tiempo-extra/", views.tiempo_extra, name="tiempo_extra"),
    path("permisos/", views.permisos, name="permisos"),
    path("permisos/", views.permisos, name="permisos"),
    
]

