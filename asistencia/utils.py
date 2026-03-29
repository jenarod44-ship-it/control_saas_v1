from datetime import datetime, timedelta
from collections import defaultdict

def calcular_horas_extra_por_dia(tiempos_extra_dia):
    total_minutos = 0

    for t in tiempos_extra_dia:
        if t.hora_fin:
            inicio = datetime.combine(t.fecha, t.hora_inicio)
            fin = datetime.combine(t.fecha, t.hora_fin)
            diferencia = fin - inicio
            total_minutos += int(diferencia.total_seconds() / 60)

    horas = total_minutos // 60
    minutos_restantes = total_minutos % 60

    if minutos_restantes >= 30:
        horas += 1

    return horas



def calcular_horas_extra_por_rango(queryset):
    por_dia = defaultdict(list)

    for t in queryset:
        por_dia[t.fecha].append(t)

    total_horas = 0

    for fecha, tiempos in por_dia.items():
        total_horas += calcular_horas_extra_por_dia(tiempos)

    return total_horas
