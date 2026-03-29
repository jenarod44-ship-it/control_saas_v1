from django.contrib import admin
from .models import Asistencia, Movimiento, TiempoExtra
admin.site.register(TiempoExtra)



@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("asistencia", "tipo", "fecha", "hora")

    def fecha_hora(self, obj):
        return f"{obj.fecha} {obj.hora}"

    fecha_hora.short_description = "Fecha y Hora"



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
       