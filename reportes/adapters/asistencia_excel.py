from core.utils.asistencia import calcular_estado_asistencia
from datetime import datetime, timedelta
from asistencia.models import Asistencia, Movimiento
from core.models import IncidenciaDia
from core.calculadora import CalculadoraAsistencia

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

def crear_reporte_asistencia_semanal(request):
    """
    Genera los datos del reporte semanal de asistencia.

    Semana operativa:
    jueves a miércoles.
    """

    from nucleo.models import Empleado

    empresa = request.empresa
    inicio = request.GET.get("inicio")

    # ==========================================
    # SEMANA OPERATIVA: JUEVES A MIERCOLES
    # ==========================================
    dias_semana = []

    if inicio:
        fecha_seleccionada = datetime.strptime(
            inicio,
            "%Y-%m-%d",
        ).date()

        dias_desde_jueves = (
            fecha_seleccionada.weekday() - 3
        ) % 7

        fecha_inicio = (
            fecha_seleccionada
            - timedelta(days=dias_desde_jueves)
        )

        dias_semana = [
            fecha_inicio + timedelta(days=i)
            for i in range(7)
        ]

    # ==========================================
    # EMPLEADOS
    # ==========================================
    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True,
    )

    departamento_id = request.GET.get("departamento")
    empleado_id = request.GET.get("empleado")

    if departamento_id and departamento_id not in ["", "0"]:
        empleados = empleados.filter(
            departamento_id=departamento_id
        )

    if empleado_id and empleado_id not in ["", "0"]:
        empleados = empleados.filter(
            id=empleado_id
        )

    empleados = empleados.order_by(
        "numero_empleado"
    )

    # ==========================================
    # ASISTENCIAS
    # ==========================================
    asistencias_semana = {}

    if dias_semana:
        asistencias_qs = Asistencia.objects.filter(
            empresa=empresa,
            empleado__in=empleados,
            fecha__range=(
                dias_semana[0],
                dias_semana[-1],
            ),
        )

        asistencias_semana = {
            (
                asistencia.empleado_id,
                asistencia.fecha,
            ): asistencia
            for asistencia in asistencias_qs
        }

    # ==========================================
    # MOVIMIENTOS
    # ==========================================
    movimientos_semana = {}

    if dias_semana:
        movimientos_qs = Movimiento.objects.filter(
            asistencia__empresa=empresa,
            asistencia__empleado__in=empleados,
            fecha__range=(
                dias_semana[0],
                dias_semana[-1],
            ),
        ).select_related(
            "asistencia",
            "asistencia__empleado",
        )

        for movimiento in movimientos_qs:
            clave = (
                movimiento.asistencia.empleado_id,
                movimiento.fecha,
            )

            movimientos_semana.setdefault(
                clave,
                [],
            ).append(movimiento)

    # ==========================================
    # INCIDENCIAS
    # ==========================================
    incidencias_semana = {}

    if dias_semana:
        incidencias_qs = IncidenciaDia.objects.filter(
            empleado__in=empleados,
            fecha__range=(
                dias_semana[0],
                dias_semana[-1],
            ),
        ).select_related(
            "empleado",
            "incidencia",
        )

        incidencias_semana = {
            (
                incidencia.empleado_id,
                incidencia.fecha,
            ): incidencia
            for incidencia in incidencias_qs
        }

    # ==========================================
    # MATRIZ SEMANAL
    # ==========================================
    matriz_semanal = []

    for empleado_matriz in empleados:
        fila = {
            "empleado": empleado_matriz,
            "dias": [],
        }

        for fecha_dia in dias_semana:
            clave = (
                empleado_matriz.id,
                fecha_dia,
            )

            asistencia_dia = asistencias_semana.get(clave)
            movimientos_dia = movimientos_semana.get(
                clave,
                [],
            )
            incidencia_dia = incidencias_semana.get(clave)

            calculadora = CalculadoraAsistencia(
                empleado_matriz,
                fecha_dia,
                movimientos=movimientos_dia,
                asistencia=asistencia_dia,
                incidencia_dia=incidencia_dia,
            )

            resultado = calculadora.calcular()

            fila["dias"].append({
                "fecha": fecha_dia,
                "entrada": resultado.get("entrada"),
                "salida": resultado.get("salida"),
                "estado": resultado.get("estado"),
                "tipo_incidencia": resultado.get(
                    "tipo_incidencia"
                ),
                "es_retardo": resultado.get("es_retardo"),
                "es_falta": resultado.get("es_falta"),
                "es_incompleto": resultado.get(
                    "es_incompleto"
                ),
                "es_irregular": resultado.get(
                    "es_irregular"
                ),
            })

        matriz_semanal.append(fila)

    return {
        "dias_semana": dias_semana,
        "empleados": empleados,
        "matriz_semanal": matriz_semanal,
    }