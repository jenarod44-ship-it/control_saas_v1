from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render

from nucleo.models import Empleado
from asistencia.models import Asistencia, TiempoExtra
from core.models import IncidenciaDia
from asistencia.models import Movimiento
from core.calculadora import CalculadoraAsistencia
from datetime import date, datetime, timedelta
from core.excel.reporte import crear_reporte_excel

@login_required
def estado_dia(request):

    empresa = request.empresa

    # 🔥 usar una sola fecha
    fecha_str = request.GET.get("fecha")

    if fecha_str:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha = timezone.localdate()

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True
    )

    reporte_dia = []

    presentes = 0
    retardos = 0
    faltas = 0

    for empleado in empleados:

        movimientos = Movimiento.objects.filter(
            asistencia__empleado=empleado,
            fecha=fecha
        ).order_by("hora")

        salida_permiso = movimientos.filter(
            tipo="SALIDA_PERMISO"
        ).last()

        regreso_permiso = movimientos.filter(
            tipo="REGRESO"
        ).last()

        extra_inicio = movimientos.filter(
            tipo="INICIO_TIEMPO_EXTRA"
        ).first()

        extra_fin = movimientos.filter(
            tipo="FIN_TIEMPO_EXTRA"
        ).first()

        calc = CalculadoraAsistencia(empleado, fecha, movimientos)
        resultado = calc.calcular()

        estado = resultado["estado"]

        if not empleado.control_horario and estado == "FALTA":
            estado = "SIN CONTROL"

        if fecha == timezone.localdate() and estado == "FALTA":

            if empleado.turno:
                ahora = timezone.localtime().time()

                limite_entrada = (
                    datetime.combine(fecha, empleado.turno.hora_entrada)
                    + timedelta(
                        minutes=empleado.turno.tolerancia_minutos
                    )
                ).time()

                if ahora <= limite_entrada:
                    estado = "PENDIENTE"

        if estado == "RETARDO":
            presentes += 1
            retardos += 1

        elif estado in [
            "ASISTENCIA",
            "OK",
            "COMPLETO",
            "INCOMPLETO",
        ]:
            presentes += 1

        elif estado == "FALTA":
            faltas += 1

        reporte_dia.append({
            "empleado": empleado,
            "entrada": resultado["entrada"],
            "permiso": (
                salida_permiso.hora
                if salida_permiso else None
            ),
            "regreso": (
                regreso_permiso.hora
                if regreso_permiso else None
            ),
            "salida": resultado["salida"],
            "horas": resultado["horas_trabajadas"],
            "estado": estado,
            "incidencia": resultado.get("incidencia"),
            "tipo_incidencia": resultado.get(
                "tipo_incidencia", ""
            ),
            "extra_inicio": (
                extra_inicio.hora
                if extra_inicio else None
            ),
            "extra_fin": (
                extra_fin.hora
                if extra_fin else None
            ),
        })

    return render(request, "control/estado_dia.html", {
        "reporte_dia": reporte_dia,
        "fecha": fecha,
        "presentes": presentes,
        "retardos": retardos,
        "faltas": faltas
    })

@login_required
def estado_dia_excel(request):

    empresa = request.empresa

    fecha_str = request.GET.get("fecha")

    if fecha_str:
        fecha = datetime.strptime(
            fecha_str,
            "%Y-%m-%d",
        ).date()
    else:
        fecha = timezone.localdate()

    empleados = Empleado.objects.filter(
        empresa=empresa,
        activo=True,
    ).order_by(
        "numero_empleado",
        "nombre",
    )

    filas = []

    for indice, empleado in enumerate(
        empleados,
        start=1,
    ):

        movimientos = Movimiento.objects.filter(
            asistencia__empleado=empleado,
            fecha=fecha,
        ).order_by("hora")

        salida_permiso = movimientos.filter(
            tipo="SALIDA_PERMISO",
        ).last()

        regreso_permiso = movimientos.filter(
            tipo="REGRESO",
        ).last()

        extra_inicio = movimientos.filter(
            tipo="INICIO_TIEMPO_EXTRA",
        ).first()

        extra_fin = movimientos.filter(
            tipo="FIN_TIEMPO_EXTRA",
        ).first()

        calc = CalculadoraAsistencia(
            empleado,
            fecha,
            movimientos,
        )

        resultado = calc.calcular()
        estado = resultado["estado"]

        if (
            not empleado.control_horario
            and estado == "FALTA"
        ):
            estado = "SIN CONTROL"

        if (
            fecha == timezone.localdate()
            and estado == "FALTA"
            and empleado.turno
        ):
            ahora = timezone.localtime().time()

            limite_entrada = (
                datetime.combine(
                    fecha,
                    empleado.turno.hora_entrada,
                )
                + timedelta(
                    minutes=(
                        empleado.turno.tolerancia_minutos
                    ),
                )
            ).time()

            if ahora <= limite_entrada:
                estado = "PENDIENTE"

        filas.append([
            indice,
            empleado.numero_empleado,
            empleado.nombre,
            resultado["entrada"] or "--",
            (
                salida_permiso.hora
                if salida_permiso
                else "--"
            ),
            (
                regreso_permiso.hora
                if regreso_permiso
                else "--"
            ),
            resultado["salida"] or "--",
            (
                extra_inicio.hora
                if extra_inicio
                else "--"
            ),
            (
                extra_fin.hora
                if extra_fin
                else "--"
            ),
            estado,
        ])

    encabezados = [
        "#",
        "No. empleado",
        "Empleado",
        "Entrada",
        "Permiso",
        "Regreso",
        "Salida",
        "Extra inicio",
        "Extra fin",
        "Estado",
    ]

    anchos = {
        1: 6,
        2: 14,
        3: 32,
        4: 12,
        5: 12,
        6: 12,
        7: 12,
        8: 13,
        9: 13,
        10: 16,
    }

    formatos = {
        4: "hh:mm",
        5: "hh:mm",
        6: "hh:mm",
        7: "hh:mm",
        8: "hh:mm",
        9: "hh:mm",
    }

    return crear_reporte_excel(
        titulo="ESTADO DEL DÍA",
        empresa=empresa,
        nombre_hoja="Estado del Día",
        nombre_archivo=(
            f"estado_del_dia_"
            f"{fecha.strftime('%Y%m%d')}.xlsx"
        ),
        encabezados=encabezados,
        filas=filas,
        anchos=anchos,
        inicio=fecha.strftime("%d/%m/%Y"),
        fin=fecha.strftime("%d/%m/%Y"),
        formatos=formatos,
        columnas_centradas=[
            1,
            2,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        ],
        columna_estado=10,
    )




    
