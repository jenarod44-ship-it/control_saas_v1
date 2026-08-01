from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render
from nucleo.models import Empleado
from .models import TiempoExtra
from asistencia.models import Asistencia, Movimiento, TiempoExtra
from django.shortcuts import redirect
from asistencia.models import Asistencia, Movimiento
from core.decorators import solo_operativo
from core.models import IncidenciaDia
from django.contrib import messages



@solo_operativo
def permisos(request):

    empresa = request.empresa
    mensaje = None

    if request.method == "POST":

        numero = request.POST.get("numero_empleado")
        tipo = request.POST.get("tipo")

        empleado = Empleado.objects.filter(
            empresa=empresa,
            numero_empleado=numero,
            activo=True,
        ).first()

        if not empleado:
            mensaje = "Empleado no encontrado"

        else:
            hoy = timezone.localdate()
            ahora = timezone.localtime()

            asistencia = Asistencia.objects.filter(
                empresa=empresa,
                empleado=empleado,
                fecha=hoy,
            ).first()

            if not asistencia:
                mensaje = "Primero debe registrar entrada"

            else:
                ultimo_movimiento = Movimiento.objects.filter(
                    asistencia=asistencia,
                    tipo__in=["SALIDA_PERMISO", "REGRESO"],
                ).order_by("-fecha", "-hora").first()

                if tipo == "SALIDA_PERMISO":

                    if (
                        ultimo_movimiento
                        and ultimo_movimiento.tipo == "SALIDA_PERMISO"
                    ):
                        mensaje = (
                            "Ya existe una salida con permiso "
                            "pendiente de regreso."
                        )

                    else:
                        Movimiento.objects.create(
                            asistencia=asistencia,
                            tipo="SALIDA_PERMISO",
                            fecha=hoy,
                            hora=ahora.time(),
                        )

                        mensaje = "Salida con permiso registrada"

                elif tipo == "REGRESO":

                    if (
                        not ultimo_movimiento
                        or ultimo_movimiento.tipo != "SALIDA_PERMISO"
                    ):
                        mensaje = (
                            "No existe una salida con permiso "
                            "pendiente de regreso."
                        )

                    else:
                        Movimiento.objects.create(
                            asistencia=asistencia,
                            tipo="REGRESO",
                            fecha=hoy,
                            hora=ahora.time(),
                        )

                        mensaje = "Regreso registrado"

                else:
                    mensaje = "Tipo de movimiento no válido"

    return render(
        request,
        "asistencia/permisos.html",
        {
            "mensaje": mensaje,
        },
    )


@solo_operativo
def tiempo_extra(request):

    from asistencia.models import Movimiento
    from django.utils import timezone

    mensaje = None

    if request.method == "POST":

        numero = request.POST.get("numero_empleado")

        if not numero:
            mensaje = "Ingrese número de empleado"
            return render(request, "asistencia/tiempo_extra.html", {"mensaje": mensaje})

        empleado = Empleado.objects.filter(
            numero_empleado=numero,
            activo=True
        ).first()

        if not empleado:
            mensaje = "Empleado no encontrado"
            return render(request, "asistencia/tiempo_extra.html", {"mensaje": mensaje})

        hoy = timezone.localdate()

        asistencia = Asistencia.objects.filter(
            empleado=empleado,
            fecha=hoy
        ).first()

        # 🔥 VALIDAR ENTRADA
        if not asistencia or not asistencia.hora_entrada:
            mensaje = "Debe registrar entrada primero"
            return render(request, "asistencia/tiempo_extra.html", {"mensaje": mensaje})
        if not asistencia.hora_salida:
            mensaje = "Debe registrar salida normal antes de iniciar tiempo extra"
            return render(request, "asistencia/tiempo_extra.html", {"mensaje": mensaje})

        movimientos = Movimiento.objects.filter(asistencia=asistencia)

        tiene_inicio = movimientos.filter(tipo="INICIO_TIEMPO_EXTRA").exists()
        tiene_fin = movimientos.filter(tipo="FIN_TIEMPO_EXTRA").exists()

        hora_actual = timezone.localtime().time()

        # 🔹 INICIO
        if not tiene_inicio:
            Movimiento.objects.create(
                asistencia=asistencia,
                tipo="INICIO_TIEMPO_EXTRA",
                hora=hora_actual,
                fecha=hoy
            )
            mensaje = f"{empleado.nombre} - Inicio de tiempo extra"

        # 🔹 FIN
        elif tiene_inicio and not tiene_fin:
            Movimiento.objects.create(
                asistencia=asistencia,
                tipo="FIN_TIEMPO_EXTRA",
                hora=hora_actual,
                fecha=hoy
            )
            mensaje = f"{empleado.nombre} - Fin de tiempo extra"

        # 🔹 YA TERMINADO
        else:
            mensaje = f"{empleado.nombre} - Tiempo extra ya registrado"

    return render(request, "asistencia/tiempo_extra.html", {
        "mensaje": mensaje
    })
            


from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from nucleo.models import Empleado
from asistencia.models import Asistencia, Movimiento


@solo_operativo
def checador(request):

    mensaje = None
    empresa = request.empresa

    if request.method == "POST":

        numero = request.POST.get("numero_empleado")

        if not numero:
            return render(
                request,
                "control/checador.html",
                {
                    "mensaje": "Ingrese número de empleado",
                },
            )

        from core.utils.laboral import es_dia_laboral

        empleado = Empleado.objects.filter(
            empresa=empresa,
            numero_empleado=numero,
            activo=True,
        ).first()

        if not empleado:
            return render(
                request,
                "control/checador.html",
                {
                    "mensaje": "Empleado no encontrado",
                },
            )

        hoy = timezone.localdate()
        now = timezone.localtime()

        # ==========================================================
        # 1. LA INCIDENCIA TIENE PRIORIDAD
        # ==========================================================
        incidencia_dia = IncidenciaDia.objects.filter(
            empleado=empleado,
            fecha=hoy,
        ).first()

        if incidencia_dia and incidencia_dia.tipo.upper() in [
            "VACACIONES",
            "INCAPACIDAD",
            "DESCANSO",
            "PERMISO",
        ]:
            mensaje = (
                "No se puede registrar asistencia. "
                f"{empleado.nombre} tiene "
                f"{incidencia_dia.tipo} registrada para hoy."
            )

            return render(
                request,
                "control/checador.html",
                {
                    "mensaje": mensaje,
                },
            )

        # ==========================================================
        # 2. VALIDAR DÍA LABORAL DESPUÉS DE LA INCIDENCIA
        # ==========================================================
        if (
            empleado.control_horario
            and not es_dia_laboral(empleado, hoy)
        ):
            mensaje = (
                f"Hoy no es un día laboral para {empleado.nombre}. "
                "Si trabajará hoy, debe registrar su jornada "
                "en Tiempo Extra."
            )

            return render(
                request,
                "control/checador.html",
                {
                    "mensaje": mensaje,
                },
            )

        asistencia = Asistencia.objects.filter(
            empresa=empresa,
            empleado=empleado,
            fecha=hoy,
        ).first()

        if not asistencia:
            asistencia = Asistencia.objects.create(
                empleado=empleado,
                empresa=empresa,
                fecha=hoy,
            )

        if not empleado.turno:
            mensaje = "Empleado sin turno asignado"

            return render(
                request,
                "control/checador.html",
                {
                    "mensaje": mensaje,
                },
            )

        movimientos = list(
            asistencia.movimientos
            .order_by("fecha", "hora")
            .values_list("tipo", flat=True)
        )

        if not asistencia.hora_entrada:
            tipo = "ENTRADA"

        else:
            if (
                "SALIDA_PERMISO" in movimientos
                and "REGRESO" not in movimientos
            ):
                mensaje = (
                    "El empleado tiene una salida con permiso pendiente. "
                    "Debe registrar el regreso antes de marcar salida."
                )

                return render(
                    request,
                    "control/checador.html",
                    {
                        "mensaje": mensaje,
                    },
                )

            if not asistencia.hora_salida:
                tipo = "SALIDA"

            else:
                mensaje = "El día ya está cerrado"

                return render(
                    request,
                    "control/checador.html",
                    {
                        "mensaje": mensaje,
                    },
                )

        # ==========================================================
        # REGISTRAR ENTRADA O SALIDA
        # ==========================================================
        if tipo == "ENTRADA":
            asistencia.hora_entrada = now.time()
            asistencia.save()

            mensaje = f"{empleado.nombre} - Entrada registrada"

        elif tipo == "SALIDA":
            asistencia.hora_salida = now.time()
            asistencia.save()

            mensaje = f"{empleado.nombre} - Salida registrada"

        Movimiento.objects.create(
            asistencia=asistencia,
            tipo=tipo,
            fecha=hoy,
            hora=now.time(),
        )

    return render(
        request,
        "control/checador.html",
        {
            "mensaje": mensaje,
        },
    )