from datetime import time
from asistencia.models import Asistencia, Movimiento
from nucleo.models import Empleado
from core.models import Incidencia
from django.utils import timezone
from core.utils.asistencia import debe_generar_falta
from datetime import datetime


def obtener_tiempo_extra(asistencia):

    movimientos = Movimiento.objects.filter(
        asistencia=asistencia
    ).order_by("hora")

    inicio = None
    fin = None

    for m in movimientos:
        if m.tipo == "INICIO_TIEMPO_EXTRA":
            inicio = m.hora
        elif m.tipo == "FIN_TIEMPO_EXTRA":
            fin = m.hora

    if not inicio:
        return None

    if not fin:
        return {
            "inicio": inicio,
            "fin": None,
            "horas": "EN CURSO"
        }

    t_inicio = datetime.combine(asistencia.fecha, inicio)
    t_fin = datetime.combine(asistencia.fecha, fin)

    diff = t_fin - t_inicio

    total_minutos = int(diff.total_seconds() / 60)

    horas_base = total_minutos // 60
    minutos = total_minutos % 60

    # 🔥 REGLA DE NEGOCIO (45 min)
    if minutos >= 45:
        horas_final = horas_base + 1
    else:
        horas_final = horas_base

    return {
        "inicio": inicio,
        "fin": fin,
        "horas": horas_final
    }

def calcular_horas_extra_por_rango(asistencias):

    total = 0

    for a in asistencias:
        info = obtener_tiempo_extra(a)

        if info and isinstance(info["horas"], int):
            total += info["horas"]

    return total


def calcular_estado_asistencia(empleado, fecha):

    if not debe_generar_falta(empleado, fecha):
        return "NO_LABORAL"

    asistencia = empleado.asistencia_set.filter(fecha=fecha).first()

    incidencia = Incidencia.objects.filter(
        empleado=empleado,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha
    ).first()

    if incidencia:
        return "INCIDENCIA"

    # 🔥 TIEMPO EXTRA REAL (por movimiento)
    if asistencia:
        movimientos = Movimiento.objects.filter(asistencia=asistencia)
        if movimientos.filter(tipo="INICIO_TIEMPO_EXTRA").exists():
            return "TIEMPO_EXTRA"

    entrada = asistencia.hora_entrada if asistencia else None
    salida = asistencia.hora_salida if asistencia else None

    hora_limite_retardo = time(8, 15)

    if entrada:

        if entrada <= hora_limite_retardo:
            estado = "OK"
        else:
            estado = "RETARDO"

        if not salida:
            estado = "INCOMPLETO"

        return estado

    if empleado.control_horario:
        return "FALTA"

    return "SIN CONTROL"

def calcular_pago_tiempo_extra(asistencias):

    total = 0

    for a in asistencias:
        info = obtener_tiempo_extra(a)

        if info and isinstance(info["horas"], int):
            horas = info["horas"]
            costo = a.empleado.costo_hora

            # 🔥 pago doble (ajustable)
            total += horas * float(costo) * 2

    return total


