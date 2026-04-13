from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.index, name="index"),
    path("asistencia/", views.reporte_asistencia, name="asistencia"),
    path("incidencias/", views.reporte_incidencias, name="incidencias"),
    path("movimientos/", views.reporte_movimientos, name="movimientos"),
    path("tiempos-extra/", views.reporte_tiempos_extra, name="tiempos_extra"),
    path("movimientos/excel/", views.exportar_movimientos_excel, name="movimientos_excel"),
    path("tiempos-extra/excel/", views.exportar_tiempos_extra_excel, name="tiempos_extra_excel"),
    path("permisos/", views.reporte_permisos, name="permisos"),
    path("permisos/excel/", views.exportar_permisos_excel, name="permisos_excel"),
    path("asistencia/excel/", views.reporte_excel, name="reporte_excel"),
    path("asistencia/excel-xlsx/", views.reporte_excel_xlsx, name="reporte_excel_xlsx"),
    path("nomina/excel/", views.exportar_nomina_excel, name="exportar_nomina_excel"),

    # Excel PRO incidencias
    path(
        "incidencias/excel/",
        views.exportar_incidencias_excel_xlsx,
        name="incidencias_excel"
    ),
    path("nomina/", views.reporte_nomina, name="reporte_nomina"),
]
