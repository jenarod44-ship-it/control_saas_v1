from django.db import models


class EmpresaQuerySet(models.QuerySet):
    def for_empresa(self, empresa):
        return self.filter(empresa=empresa)


class EmpresaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def for_empresa(self, empresa):
        return self.get_queryset().filter(empresa=empresa)
