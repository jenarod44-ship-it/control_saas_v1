from django.db import models
from core.models import Empresa


class Asistencia(models.Model):
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)
    empleado = models.ForeignKey("nucleo.Empleado", on_delete=models.CASCADE)

    fecha = models.DateField()
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_salida = models.TimeField(null=True, blank=True)

    TIPO_DIA = [
        ("NORMAL", "Normal"),
        ("PERMISO", "Permiso"),
        ("VACACIONES", "Vacaciones"),
        ("INCAPACIDAD", "Incapacidad"),
    ]

    tipo_dia = models.CharField(max_length=20, choices=TIPO_DIA, default="NORMAL")

    class Meta:
        unique_together = ("empresa", "empleado", "fecha")

    def __str__(self):
        return f"{self.empleado} - {self.fecha}"
