from django.urls import path
from .views import lista_movimientos

app_name = "movimientos"

urlpatterns = [
    path("", lista_movimientos, name="movimientos_lista"),
]
