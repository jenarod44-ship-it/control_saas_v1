from datetime import time
from asistencia.models import Asistencia
from nucleo.models import Empleado
from core.models import Incidencia
from django.utils import timezone


def calcular_estado_asistencia(empleado, fecha):

    asistencia = Asistencia.objects.filter(
        empleado=empleado,
        fecha=fecha
    ).first()

    incidencia = Incidencia.objects.filter(
        empleado=empleado,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha
    ).first()

    entrada = asistencia.hora_entrada if asistencia else None
    salida = asistencia.hora_salida if asistencia else None

    hora_limite_retardo = time(8, 15)

    if incidencia:
        return "INCIDENCIA"

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
