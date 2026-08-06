from core.excel.estilos import (
    RELLENO_ALERTA,
    RELLENO_ERROR,
    RELLENO_GRIS,
    RELLENO_INFORMATIVO,
)
from reportes.services.incidencias import obtener_incidencias


COLORES_TIPO_INCIDENCIA = {
    "VACACIONES": RELLENO_INFORMATIVO,
    "INCAPACIDAD": RELLENO_ERROR,
    "DESCANSO": RELLENO_GRIS,
    "PERMISO": RELLENO_ALERTA,
}


def construir_reporte_incidencias(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    incidencias = obtener_incidencias(
        empresa=empresa,
        inicio=inicio,
        fin=fin,
        empleado_id=empleado_id,
    )

    filas = []

    for incidencia in incidencias:
        filas.append([
            incidencia.empleado.numero_empleado,
            incidencia.empleado.nombre,
            incidencia.tipo,
            incidencia.fecha_inicio,
            incidencia.fecha_fin,
        ])

    return {
        "titulo": "REPORTE DE INCIDENCIAS",
        "empresa": empresa,
        "nombre_hoja": "Incidencias",
        "nombre_archivo": "reporte_incidencias.xlsx",
        "inicio": inicio,
        "fin": fin,
        "encabezados": [
            "No. Empleado",
            "Empleado",
            "Tipo",
            "Fecha Inicio",
            "Fecha Fin",
        ],
        "filas": filas,
        "anchos": {
            1: 14,
            2: 35,
            3: 18,
            4: 14,
            5: 14,
        },
        "formatos": {
            4: "dd/mm/yyyy",
            5: "dd/mm/yyyy",
        },
        "columnas_centradas": [
            1,
            3,
            4,
            5,
        ],
        "reglas_color": {
            3: COLORES_TIPO_INCIDENCIA,
        },
    }