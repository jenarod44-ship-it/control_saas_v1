from django.contrib import admin
from .models import Asistencia


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):

    fields = ('empleado', 'fecha', 'hora_entrada', 'hora_salida')

    def save_model(self, request, obj, form, change):
        if not obj.empresa:
            obj.empresa = request.empresa
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.empresa:
            return qs.filter(empresa=request.empresa)
        return qs