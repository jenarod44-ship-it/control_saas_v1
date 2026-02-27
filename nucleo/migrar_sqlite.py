from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = "Migrar datos desde SQLite a PostgreSQL"

    def handle(self, *args, **kwargs):
    models = apps.get_models()

    for model in models:
        self.stdout.write(f"Modelo detectado: {model.__name__}")

        objs = model.objects.using("sqlite").all()
        self.stdout.write(f"  Registros: {objs.count()}")

        for obj in objs:
            obj.pk = None
            obj.save(using="default")

    self.stdout.write(self.style.SUCCESS("Migración completa"))