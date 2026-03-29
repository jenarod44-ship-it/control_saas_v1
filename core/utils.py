from core.models import Perfil
from datetime import time
from asistencia.models import Asistencia
from core.models import Incidencia
from django.utils import timezone
from asistencia.models import Asistencia, Movimiento, TiempoExtra
from asistencia.models import Movimiento

def calcular_incidencias_asistencia(empleado, fecha):
    incidencias = []

    asistencias = empleado.asistencia_set.filter(fecha=fecha).first()

    if not asistencias:
        incidencias.append("FALTA")
        return incidencias

    if not asistencias.hora_entrada:
        incidencias.append("SIN ENTRADA")

    if not asistencias.hora_salida:
        incidencias.append("SIN SALIDA")

    return incidencias


from datetime import datetime, timedelta

from datetime import datetime, timedelta
from asistencia.models import Movimiento


def calcular_estado_asistencia(empleado, fecha):

    asistencia = empleado.asistencia_set.filter(fecha=fecha).first()

    if not asistencia:
        return "FALTA"

    if not asistencia.hora_entrada:
        return "FALTA"

    turno = empleado.turno

    if not turno:
        return "SIN TURNO"

    movimientos = Movimiento.objects.filter(asistencia=asistencia)

    tiene_salida_permiso = movimientos.filter(tipo="SALIDA_PERMISO").exists()
    tiene_regreso = movimientos.filter(tipo="REGRESO").exists()
    tiene_tiempo_extra = movimientos.filter(tipo="INICIO_TIEMPO_EXTRA").exists()

    if not asistencia.hora_salida:

        if tiene_salida_permiso and not tiene_regreso:
            return "PERMISO"

        if tiene_tiempo_extra:
            return "TIEMPO EXTRA"

        return "INCOMPLETO"

    entrada_real = datetime.combine(fecha, asistencia.hora_entrada)
    entrada_turno = datetime.combine(fecha, turno.hora_entrada)

    tolerancia = timedelta(minutes=10)

    if entrada_real <= entrada_turno + tolerancia:
        return "OK"
    else:
        return "RETARDO"

from datetime import datetime

def calcular_tiempo(salida, regreso):

    if not salida or not regreso:
        return ""

    t_salida = datetime.combine(datetime.today(), salida)
    t_regreso = datetime.combine(datetime.today(), regreso)

    diferencia = t_regreso - t_salida

    horas = diferencia.seconds // 3600
    minutos = (diferencia.seconds % 3600) // 60

    return f"{horas:02d}:{minutos:02d}"

    

def obtener_empresa_usuario(user):
    if hasattr(user, "perfil_core"):
        return user.perfil_core.empresa
    return None

app_name = "core"

def empleado_trabaja(empleado, fecha):

    dia = fecha.weekday()

    dias = empleado.dias_trabajo.split(",")

    return str(dia) in dias
