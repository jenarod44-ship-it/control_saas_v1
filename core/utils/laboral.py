def es_dia_laboral(empleado, fecha):

    

    dia = fecha.weekday()  # 0=lunes ... 6=domingo

    # 🔥 SI EL DEPARTAMENTO TRABAJA FINES → SIEMPRE LABORAL
    if empleado.departamento and getattr(empleado.departamento, "trabaja_fines_semana", False):
        return True

    # 🔥 lógica normal por días
    dias = empleado.dias_trabajo.split(",") if empleado.dias_trabajo else []

    return str(dia) in dias
