from django.db import models
from django.contrib.auth.models import User



class Empresa(models.Model):
    nombre = models.CharField(max_length=150)
    subdominio = models.CharField(max_length=50, unique=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_core")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Incidencia(models.Model):

    empleado = models.ForeignKey("nucleo.Empleado", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=30)

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __str__(self):
        return f"{self.empleado} | {self.tipo} | {self.fecha_inicio} - {self.fecha_fin}"

class IncidenciaDia(models.Model):

    empleado = models.ForeignKey("nucleo.Empleado", on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo = models.CharField(max_length=30)

    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.CASCADE,
        related_name="dias"
    )

    class Meta:
        unique_together = ("empleado", "fecha")

    def __str__(self):
        return f"{self.empleado} - {self.fecha} - {self.tipo}"


