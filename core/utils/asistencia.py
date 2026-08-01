from core.utils.laboral import es_dia_laboral
from datetime import datetime, timedelta
from asistencia.models import Asistencia, Movimiento
from core.models import Incidencia, IncidenciaDia



def debe_generar_falta(empleado, fecha):
    """
    Determina si se debe generar falta para un empleado en una fecha.
    """

    # 🔥 Si no es día laboral → NO falta
    if not es_dia_laboral(empleado, fecha):
        return False

    return True


def es_tiempo_extra(empleado, fecha):

    dia = fecha.weekday()

    # 🔥 Si es fin de semana
    if dia in [5, 6]:

        # 🔥 Si normalmente NO trabaja ese día
        if not es_dia_laboral(empleado, fecha):
            return True

    return False

def calcular_estado_asistencia(empleado, fecha):

    # =========================
    # 1. REVISAR INCIDENCIA
    # =========================
    incidencia_dia = IncidenciaDia.objects.filter(
        empleado=empleado,
        fecha=fecha,
    ).first()

    if incidencia_dia:
        return "INCIDENCIA"

    incidencia_rango = Incidencia.objects.filter(
        empleado=empleado,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha,
    ).first()

    if incidencia_rango:
        return "INCIDENCIA"

    # =========================
    # 2. BUSCAR ASISTENCIA
    # =========================
    asistencia = empleado.asistencia_set.filter(
        fecha=fecha,
    ).first()

    # =========================
    # 3. EMPLEADO SIN CONTROL
    # =========================
    if not empleado.control_horario:

        if not asistencia or not asistencia.hora_entrada:
            return "FALTA"

        if not asistencia.hora_salida:
            return "INCOMPLETO"

        return "OK"

    # =========================
    # 4. DÍA NO LABORAL
    # =========================
    if not debe_generar_falta(empleado, fecha):
        return "NO_LABORAL"

    # =========================
    # 5. ASISTENCIA
    # =========================
    if not asistencia:
        return "FALTA"

    if not asistencia.hora_entrada:
        return "FALTA"

    turno = empleado.turno

    if not turno:
        return "SIN TURNO"

    movimientos = Movimiento.objects.filter(
        asistencia=asistencia,
    )

    tiene_salida_permiso = movimientos.filter(
        tipo="SALIDA_PERMISO",
    ).exists()

    tiene_regreso = movimientos.filter(
        tipo="REGRESO",
    ).exists()

    tiene_tiempo_extra = movimientos.filter(
        tipo="INICIO_TIEMPO_EXTRA",
    ).exists()

    # =========================
    # 6. TIEMPO EXTRA
    # =========================
    if es_tiempo_extra(empleado, fecha):
        return "TIEMPO_EXTRA"

    # =========================
    # 7. ASISTENCIA INCOMPLETA
    # =========================
    if not asistencia.hora_salida:

        if tiene_salida_permiso and not tiene_regreso:
            return "PERMISO"

        if tiene_tiempo_extra:
            return "TIEMPO_EXTRA"

        return "INCOMPLETO"

    # =========================
    # 8. PUNTUALIDAD
    # =========================
    entrada_real = datetime.combine(
        fecha,
        asistencia.hora_entrada,
    )

    entrada_turno = datetime.combine(
        fecha,
        turno.hora_entrada,
    )

    tolerancia = timedelta(
        minutes=turno.tolerancia_minutos,
    )

    if entrada_real <= entrada_turno + tolerancia:
        return "OK"

    return "RETARDO"

