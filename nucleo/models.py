from django.db import models
from django.utils import timezone


class Empleado(models.Model):
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    numero_empleado = models.CharField(max_length=10)
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = "nucleo"
        unique_together = ('empresa', 'numero_empleado')

    def __str__(self):
        return f"{self.numero_empleado} - {self.nombre}"



from django.db import models
from django.utils import timezone


class Empleado(models.Model):
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    numero_empleado = models.CharField(max_length=10)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('empresa', 'numero_empleado')

    def __str__(self):
        return f"{self.numero_empleado} - {self.nombre}"












