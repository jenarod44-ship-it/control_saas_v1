from django.db import models
from django.utils import timezone
from .managers import EmpresaManager


class Departamento(models.Model):

    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    objects = EmpresaManager()   # 👈 FALTA ESTO

    def __str__(self):
        return self.nombre



class Empleado(models.Model):

    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    control_horario = models.BooleanField(default=True)
    nombre = models.CharField(max_length=100)
    numero_empleado = models.CharField(max_length=10)
    activo = models.BooleanField(default=True)

    dias_trabajo = models.CharField(max_length=20, default="0,1,2,3,4")

    turno = models.ForeignKey(
        "core.Turno",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    costo_hora = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    objects = EmpresaManager()   # 👈 🔥 ESTE ES EL IMPORTANTE

    class Meta:
        unique_together = ("empresa", "numero_empleado")

    def __str__(self):
        return f"{self.numero_empleado} - {self.nombre}"    

    
    
    












