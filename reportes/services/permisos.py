from asistencia.models import Movimiento


def obtener_resultados_permisos(
    empresa,
    inicio=None,
    fin=None,
    empleado_id=None,
):
    movimientos = Movimiento.objects.filter(
        tipo__in=[
            "SALIDA_PERMISO",
            "REGRESO",
        ],
        asistencia__empleado__empresa=empresa,
    ).select_related(
        "asistencia",
        "asistencia__empleado",
    )

    if inicio:
        movimientos = movimientos.filter(
            fecha__gte=inicio,
        )

    if fin:
        movimientos = movimientos.filter(
            fecha__lte=fin,
        )

    if empleado_id and empleado_id != "0":
        movimientos = movimientos.filter(
            asistencia__empleado_id=empleado_id,
        )

    movimientos = movimientos.order_by(
        "asistencia__empleado__numero_empleado",
        "fecha",
        "hora",
    )

    permisos_abiertos = {}
    resultados = []

    for movimiento in movimientos:
        clave = (
            movimiento.asistencia_id,
            movimiento.fecha,
        )

        if movimiento.tipo == "SALIDA_PERMISO":
            permisos_abiertos[clave] = {
                "numero_empleado": (
                    movimiento.asistencia.empleado.numero_empleado
                ),
                "empleado": (
                    movimiento.asistencia.empleado.nombre
                ),
                "fecha": movimiento.fecha,
                "salida": movimiento.hora,
                "regreso": None,
            }

        elif (
            movimiento.tipo == "REGRESO"
            and clave in permisos_abiertos
        ):
            permiso = permisos_abiertos.pop(clave)
            permiso["regreso"] = movimiento.hora
            resultados.append(permiso)

    # Incluir permisos todavía pendientes de regreso.
    resultados.extend(
        permisos_abiertos.values()
    )

    resultados.sort(
        key=lambda registro: (
            str(registro["numero_empleado"]),
            registro["fecha"],
            registro["salida"],
        )
    )

    return resultados