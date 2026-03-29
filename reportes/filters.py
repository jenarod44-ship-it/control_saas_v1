from checador.models import Checada


def filtrar_asistencias(request):

    fecha_inicio = request.GET.get("inicio")
    fecha_fin = request.GET.get("fin")

    queryset = Checada.objects.all()

    if fecha_inicio and fecha_fin:
        queryset = queryset.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        )

    return queryset
