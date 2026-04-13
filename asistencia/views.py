from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render
from nucleo.models import Empleado
from .models import TiempoExtra
from asistencia.models import Asistencia, Movimiento, TiempoExtra
from django.shortcuts import redirect
from asistencia.models import Asistencia, Movimiento
from core.decorators import solo_operativo



@solo_operativo
def permisos(request):
    

    mensaje = None

    if request.method == "POST":

        numero = request.POST.get("numero_empleado")
        tipo = request.POST.get("tipo")

        print("👉 NUMERO:", numero)
        print("👉 TIPO:", tipo)

        empleado = Empleado.objects.filter(
            numero_empleado=numero,
            activo=True
        ).first()

        if not empleado:
            mensaje = "Empleado no encontrado"

        else:
            hoy = timezone.localdate()
            now = timezone.localtime()

            asistencia = Asistencia.objects.filter(
                empleado=empleado,
                fecha=hoy
            ).first()

            print("👉 ASISTENCIA:", asistencia)

            if not asistencia:
                mensaje = "Primero debe registrar entrada"

            else:
                Movimiento.objects.create(
                    asistencia=asistencia,
                    tipo=tipo,
                    fecha=hoy,
                    hora=now.time()
                )

                print("🔥 MOVIMIENTO CREADO")

                if tipo == "SALIDA_PERMISO":
                    mensaje = "Salida con permiso registrada"
                else:
                    mensaje = "Regreso registrado"

    return render(request, "asistencia/permisos.html", {
        "mensaje": mensaje
    })
                


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

    if request.method == "POST":

        numero = request.POST.get("numero_empleado")

        if not numero:
            return render(request, "control/checador.html", {
                "mensaje": "Ingrese número de empleado"
            })

        empleado = Empleado.objects.filter(
            numero_empleado=numero,
            activo=True
        ).first()

        if not empleado:
            return render(request, "control/checador.html", {
                "mensaje": "Empleado no encontrado"
            })

        hoy = timezone.localdate()
        now = timezone.localtime()

        asistencia = Asistencia.objects.filter(
            empleado=empleado,
            fecha=hoy
        ).first()

        if not asistencia:
            asistencia = Asistencia.objects.create(
                empleado=empleado,
                empresa=empleado.empresa,
                fecha=hoy
            )

        # 🔥 LÓGICA SIMPLE
        if not asistencia.hora_entrada:
            tipo = "ENTRADA"

        elif not asistencia.hora_salida:
            tipo = "SALIDA"

        else:
            mensaje = "El día ya está cerrado"
            return render(request, "control/checador.html", {
                "mensaje": mensaje
            })

        # 🔥 REGISTRAR
        if tipo == "ENTRADA":
            asistencia.hora_entrada = now.time()
            asistencia.save()
            mensaje = f"{empleado.nombre} - Entrada registrada"

        elif tipo == "SALIDA":
            asistencia.hora_salida = now.time()
            asistencia.save()
            mensaje = f"{empleado.nombre} - Salida registrada"

        # 🔥 MOVIMIENTO (solo registro)
        Movimiento.objects.create(
            asistencia=asistencia,
            tipo=tipo,
            fecha=hoy,
            hora=now.time()
        )

    return render(request, "control/checador.html", {
        "mensaje": mensaje
    })