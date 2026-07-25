def es_dia_laboral(empleado, fecha):
    """
    Indica si una fecha es laborable para un empleado.

    Los días se obtienen de empleado.dias_trabajo:
    0 = lunes
    1 = martes
    2 = miércoles
    3 = jueves
    4 = viernes
    5 = sábado
    6 = domingo
    """

    if not empleado or not fecha:
        return False

    dias_configurados = empleado.dias_trabajo or ""

    dias_laborales = {
        dia.strip()
        for dia in dias_configurados.split(",")
        if dia.strip() in {"0", "1", "2", "3", "4", "5", "6"}
    }

    return str(fecha.weekday()) in dias_laborales