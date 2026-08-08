from core.excel.estilos import (
    RELLENO_ALERTA,
    RELLENO_ERROR,
    RELLENO_GRIS,
    RELLENO_INFORMATIVO,
    RELLENO_OK,
)
from core.services.prenomina_service import ResumenPrenomina


def construir_reporte_prenomina(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    departamento_id = request.GET.get("departamento")
    empleado_id = request.GET.get("empleado")

    resultados = ResumenPrenomina(
        empresa=empresa,
        fecha_inicio=inicio,
        fecha_fin=fin,
        departamento_id=departamento_id or None,
        empleado_id=empleado_id or None,
    ).generar()

    filas = []

    totales = {
        "dias_laborados": 0,
        "no_laborales": 0,
        "faltas": 0,
        "vacaciones": 0,
        "incapacidades": 0,
        "descansos": 0,
        "permisos": 0,
        "dias_a_pagar": 0,
        "total_fila": 0,
        "dias_periodo": 0,
        "retardos": 0,
        "salidas_permiso": 0,
        "horas_trabajadas": 0,
        "tiempo_extra": 0,
    }

    for registro in resultados:

        filas.append([
            registro["numero_empleado"],
            registro["empleado"],
            registro["departamento"],
            registro["turno"],
            registro["dias_laborados"],
            registro["no_laborales"],
            registro["faltas"],
            registro["vacaciones"],
            registro["incapacidades"],
            registro["descansos"],
            registro["permisos"],
            registro["dias_a_pagar"],
            registro["total_fila"],
            registro["dias_periodo"],
            registro["retardos"],
            registro["salidas_permiso"],
            registro["horas_trabajadas"],
            registro["tiempo_extra"],
        ])

        for clave in totales:
            valor = registro.get(clave, 0) or 0

            if isinstance(valor, (int, float)):
                totales[clave] += valor

    fila_totales = [
        "TOTALES GENERALES",
        "",
        "",
        "",
        totales["dias_laborados"],
        totales["no_laborales"],
        totales["faltas"],
        totales["vacaciones"],
        totales["incapacidades"],
        totales["descansos"],
        totales["permisos"],
        totales["dias_a_pagar"],
        totales["total_fila"],
        totales["dias_periodo"],
        totales["retardos"],
        totales["salidas_permiso"],
        round(totales["horas_trabajadas"], 2),
        round(totales["tiempo_extra"], 2),
    ]

    return {
        "titulo": "RESUMEN SEMANAL DE PRE-NÓMINA",
        "empresa": empresa,
        "nombre_hoja": "Pre-Nómina",
        "nombre_archivo": "resumen_pre_nomina.xlsx",
        "inicio": inicio,
        "fin": fin,

        "encabezados": [
            "No. Empleado",
            "Empleado",
            "Departamento",
            "Turno",
            "Días Trabajados",
            "Días de Descanso",
            "Faltas",
            "Vacaciones",
            "Incapacidades",
            "Licencias",
            "Permisos",
            "Días a Pagar",
            "Días Clasificados",
            "Período",
            "Retardos",
            "Salidas Permiso",
            "Horas Trabajadas",
            "Tiempo Extra",
        ],

        "filas": filas,

        "anchos": {
            1: 14,
            2: 32,
            3: 24,
            4: 20,
            5: 15,
            6: 16,
            7: 9,
            8: 12,
            9: 15,
            10: 11,
            11: 10,
            12: 14,
            13: 17,
            14: 10,
            15: 10,
            16: 16,
            17: 17,
            18: 13,
        },

        "formatos": {
            17: "0.00",
            18: "0.00",
        },

        "columnas_centradas": [
            1,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
        ],

        "columnas_relleno_fijo": {
            14: RELLENO_GRIS,
        },

        "reglas_condicionales": [
            {
                "columna": 12,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_OK,
            },
            {
                "columna": 7,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_ERROR,
            },
            {
                "columna": 8,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_INFORMATIVO,
            },
            {
                "columna": 9,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_ERROR,
            },
            {
                "columna": 10,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_GRIS,
            },
            {
                "columna": 11,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_ALERTA,
            },
            {
                "columna": 13,
                "condicion": lambda valor, valores: (
                    (valor or 0) == (valores[13] or 0)
                ),
                "relleno": RELLENO_OK,
            },
            {
                "columna": 13,
                "condicion": lambda valor, valores: (
                    (valor or 0) != (valores[13] or 0)
                ),
                "relleno": RELLENO_ERROR,
            },
            {
                "columna": 15,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_ALERTA,
            },
            {
                "columna": 16,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_INFORMATIVO,
            },
            {
                "columna": 18,
                "condicion": lambda valor, valores: (valor or 0) > 0,
                "relleno": RELLENO_OK,
            },
        ],

        "mostrar_total": False,
        "fila_totales": fila_totales,
    }