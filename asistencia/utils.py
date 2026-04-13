from datetime import datetime, timedelta
from collections import defaultdict

from collections import defaultdict
from datetime import datetime
from asistencia.models import Movimiento


def calcular_horas_extra_por_dia(asistencia):

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

    if not inicio or not fin:
        return 0

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

    return horas_final



def calcular_horas_extra_por_rango(asistencias):

    total = 0

    for a in asistencias:
        total += calcular_horas_extra_por_dia(a)

    return total