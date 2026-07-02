from django.db import models
from django.contrib.auth.models import User



class Empresa(models.Model):
    nombre = models.CharField("Nombre comercial", max_length=150)
    razon_social = models.CharField("Razón social", max_length=200, blank=True)
    rfc = models.CharField("RFC", max_length=20, blank=True)

    subdominio = models.CharField("Subdominio", max_length=50, unique=True)
    activa = models.BooleanField("Empresa activa", default=True)

    fecha_alta = models.DateTimeField("Fecha de alta", auto_now_add=True)

    def __str__(self):
        return self.nombre


class Perfil(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_core"
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

class Incidencia(models.Model):

    turno = models.ForeignKey(
        "core.Turno",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    empleado = models.ForeignKey("nucleo.Empleado", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=100)

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __str__(self):
        return f"{self.empleado} | {self.tipo} | {self.fecha_inicio} - {self.fecha_fin}"

class IncidenciaDia(models.Model):

    empleado = models.ForeignKey("nucleo.Empleado", on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo = models.CharField(max_length=100)

    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.CASCADE,
        related_name="dias"
    )
class Turno(models.Model):
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)

    nombre = models.CharField(max_length=100)

    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    tolerancia_minutos = models.IntegerField(default=5)

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.hora_entrada} - {self.hora_salida})"

    class Meta:
        unique_together = ("empresa", "nombre")
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ("empresa__nombre", "nombre")
class EmpresaUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("usuario", "empresa")
        verbose_name = "Usuario-Empresa"
        verbose_name_plural = "Usuarios-Empresa"

    def __str__(self):
        return f"{self.usuario.username} → {self.empresa.nombre}"


