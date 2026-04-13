from core.utils.laboral import es_dia_laboral


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