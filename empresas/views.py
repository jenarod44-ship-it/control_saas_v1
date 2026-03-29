
empleados = Empleado.objects.filter(
    empresa=empresa
).order_by("numero_empleado")

