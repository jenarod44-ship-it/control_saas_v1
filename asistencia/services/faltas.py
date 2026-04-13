from core.utils.laboral import es_dia_laboral

def debe_generar_falta(empleado, fecha):
    return es_dia_laboral(empleado, fecha)
