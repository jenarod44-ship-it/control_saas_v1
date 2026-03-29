from django.db import models

class EmpresaManager(models.Manager):

    def para_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)
