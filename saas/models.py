from django.db import models

# Create your models here.
from django.db import models

class Empresa(models.Model):
    nombre = models.CharField(max_length=150)
    rfc = models.CharField(max_length=20, blank=True, null=True)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class TenantModel(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    class Meta:
        abstract = True
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_saas"
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.empresa.nombre}"
class TenantManager(models.Manager):
    def for_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)