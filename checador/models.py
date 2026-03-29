from django.db import models

hora_fin = models.TimeField(null=True, blank=True)


class Checada(models.Model):

    empleado = models.CharField(max_length=150)
    fecha = models.DateField()
    entrada = models.TimeField(null=True, blank=True)
    salida = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.empleado} - {self.fecha}"
