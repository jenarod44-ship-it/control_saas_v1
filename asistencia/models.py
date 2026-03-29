from core.models import Empresa
from django.db import models
from datetime import datetime, date


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

    tipo_dia = models.CharField(
        max_length=20,
        choices=TIPO_DIA,
        default="NORMAL"
    )

    def estado_display(self):

        # 🥇 PRIORIDAD 1 — INCIDENCIAS
        if self.tipo_dia and self.tipo_dia != "NORMAL":
            return self.tipo_dia

        # 🥈 PRIORIDAD 2 — ASISTENCIA
        if self.hora_entrada and not self.hora_salida:
            return "INCOMPLETO"

        if self.hora_entrada and self.hora_salida:
            return "COMPLETO"

        # 🥉 PRIORIDAD 3 — FALTA
        return "FALTA"

    class Meta:
        unique_together = ("empresa", "empleado", "fecha")

    def __str__(self):
        return f"{self.empleado} - {self.fecha}"
    


class TiempoExtra(models.Model):

    empleado = models.ForeignKey("nucleo.Empleado", on_delete=models.CASCADE)

    asistencia = models.ForeignKey(
        "asistencia.Asistencia",
        on_delete=models.CASCADE
    )

    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField(null=True, blank=True)

    horas = models.FloatField(null=True, blank=True)

    from datetime import datetime, date

    def calcular_horas(self):

        if not self.hora_inicio or not self.hora_fin:
            return 0

        inicio = datetime.combine(date.min, self.hora_inicio)
        fin = datetime.combine(date.min, self.hora_fin)

        diferencia = fin - inicio

        minutos = diferencia.total_seconds() / 60

        # 🔥 HORAS COMPLETAS
        horas = int(minutos // 60)
        resto = minutos % 60

        # 🔥 REGLA NUEVA
        if resto >= 45:
            horas += 1

        return horas

    def save(self, *args, **kwargs):
        self.horas = self.calcular_horas()
        super().save(*args, **kwargs)   


    def __str__(self):
        return f"{self.empleado} - {self.fecha}"
    

class Movimiento(models.Model):

    TIPOS = [
    ("ENTRADA", "Entrada"),
    ("SALIDA", "Salida"),
    ("SALIDA_PERMISO", "Salida con permiso"),
    ("REGRESO", "Regreso"),
]

    asistencia = models.ForeignKey(
        "asistencia.Asistencia",
        on_delete=models.CASCADE,
        related_name="movimientos"
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS
    )

    fecha = models.DateField()
    hora = models.TimeField()

    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "hora"]

    def __str__(self):
        return f"{self.asistencia.empleado} - {self.tipo} - {self.fecha} {self.hora}"
    
    

