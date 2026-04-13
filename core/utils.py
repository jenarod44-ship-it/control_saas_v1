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


from core.utils.asistencia import debe_generar_falta, es_tiempo_extra
from datetime import datetime, timedelta

def calcular_estado_asistencia(empleado, fecha):

    # 🔥 validar si es día laboral
    if not debe_generar_falta(empleado, fecha):
        return "NO_LABORAL"

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

    # 🔥 NUEVO: tiempo extra por día
    if es_tiempo_extra(empleado, fecha):
        return "TIEMPO_EXTRA"

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

    

def obtener_empresa_actual(request):
    empresa_id = request.session.get("empresa_id")

    if empresa_id:
        return Empresa.objects.filter(id=empresa_id).first()

    relacion = EmpresaUsuario.objects.filter(
        usuario=request.user
    ).first()

    return relacion.empresa if relacion else None

def empleado_trabaja(empleado, fecha):

    dia = fecha.weekday()

    dias = empleado.dias_trabajo.split(",")

    return str(dia) in dias

