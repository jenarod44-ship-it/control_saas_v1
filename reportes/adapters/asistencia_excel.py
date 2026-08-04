from core.utils.asistencia import calcular_estado_asistencia
from reportes.services.asistencia import (
    aplicar_filtros_asistencia,
    calcular_incidencias_asistencia,
    obtener_asistencias_base,
)
from core.excel.estilos import (
    RELLENO_ALERTA,
    RELLENO_ERROR,
    RELLENO_GRIS,
    RELLENO_INFORMATIVO,
    RELLENO_OK,
)
from core.utils.asistencia import calcular_estado_asistencia
from reportes.services.asistencia import (
    aplicar_filtros_asistencia,
    calcular_incidencias_asistencia,
    obtener_asistencias_base,
)


COLORES_ESTADO = {
    "OK": RELLENO_OK,
    "ASISTENCIA": RELLENO_OK,
    "COMPLETO": RELLENO_OK,

    "RETARDO": RELLENO_ALERTA,

    "FALTA": RELLENO_ERROR,

    "INCOMPLETO": RELLENO_INFORMATIVO,
    "PENDIENTE": RELLENO_INFORMATIVO,
    "TIEMPO_EXTRA": RELLENO_INFORMATIVO,

    "VACACIONES": RELLENO_GRIS,
    "INCAPACIDAD": RELLENO_GRIS,
    "DESCANSO": RELLENO_GRIS,
    "PERMISO": RELLENO_GRIS,
    "INCIDENCIA": RELLENO_GRIS,
    "NO_LABORAL": RELLENO_GRIS,
    "SIN CONTROL": RELLENO_GRIS,
    "SIN_TURNO": RELLENO_GRIS,
}


COLORES_INCIDENCIA = {
    "OK": RELLENO_OK,
    "SIN SALIDA": RELLENO_ERROR,
    "RETARDO": RELLENO_ALERTA,
    "SIN TURNO": RELLENO_GRIS,
}

def construir_reporte_asistencia(request):
    empresa = request.empresa
    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")

    registros = obtener_asistencias_base(request)
    registros = aplicar_filtros_asistencia(
        request,
        registros,
    ).order_by(
        "empleado__numero_empleado",
        "-fecha",
    )

    
    filas = []

    for registro in registros:
        estado = calcular_estado_asistencia(
            registro.empleado,
            registro.fecha,
        )

        incidencias = calcular_incidencias_asistencia(
            registro.empleado,
            registro.fecha,
        )

        incidencia_texto = (
            " | ".join(incidencias)
            if incidencias
            else "OK"
        )

        filas.append([
            registro.empleado.numero_empleado,
            registro.empleado.nombre,
            registro.fecha,
            registro.hora_entrada or "--",
            registro.hora_salida or "--",
            estado,
            incidencia_texto,
        ])

    return {
        "titulo": "REPORTE DE ASISTENCIA",
        "empresa": empresa,
        "nombre_hoja": "Asistencia",
        "nombre_archivo": "reporte_asistencia.xlsx",
        "inicio": inicio,
        "fin": fin,
        "encabezados": [
            "No. Empleado",
            "Empleado",
            "Fecha",
            "Hora Entrada",
            "Hora Salida",
            "Estado",
            "Incidencias",
        ],
        "filas": filas,
        "anchos": {
            1: 14,
            2: 35,
            3: 13,
            4: 14,
            5: 14,
            6: 16,
            7: 38,
        },
        "formatos": {
            3: "dd/mm/yyyy",
            4: "hh:mm",
            5: "hh:mm",
        },
        "columnas_centradas": [
            1,
            3,
            4,
            5,
            6,
        ],
        "columnas_envueltas": [
            7,
        ],
        "reglas_color": {
            6: COLORES_ESTADO,
            7: COLORES_INCIDENCIA,
        },
    }