def construir_reporte_permisos(request):

    empresa = request.empresa

    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    empleado_id = request.GET.get("empleado")

    resultados = obtener_resultados_permisos(
        empresa=empresa,
        inicio=inicio,
        fin=fin,
        empleado_id=empleado_id,
    )

    filas = []

    for r in resultados:

        filas.append([
            r["numero_empleado"],
            r["empleado"],
            r["fecha"],
            r["salida"] or "--",
            r["regreso"] or "--",
        ])

    return {

        "titulo": "REPORTE DE PERMISOS",

        "empresa": empresa,

        "inicio": inicio,
        "fin": fin,

        "encabezados": [

            "No. Empleado",
            "Empleado",
            "Fecha",
            "Salida",
            "Regreso",

        ],

        "filas": filas,

        "nombre_hoja": "Permisos",

        "nombre_archivo": "reporte_permisos.xlsx",

        "anchos": {

            "A":14,
            "B":35,
            "C":13,
            "D":12,
            "E":12,

        },

        "columnas_fecha":[3],

        "columnas_hora":[4,5],

        "columnas_color":{

            4:"ALERTA",
            5:"PERMISO",

        }

    }