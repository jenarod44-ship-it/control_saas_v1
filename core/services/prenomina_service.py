from collections import defaultdict
from datetime import datetime, timedelta
from asistencia.models import Asistencia, Movimiento, TiempoExtra
from core.models import IncidenciaDia
from nucleo.models import Empleado
from django.utils import timezone
from core.calculadora import CalculadoraAsistencia
from core.utils.laboral import es_dia_laboral
from core.utils.asistencia import calcular_estado_asistencia
from datetime import datetime


class ResumenPrenomina:

    def __init__(
        self,
        empresa,
        fecha_inicio,
        fecha_fin,
        departamento_id=None,
        empleado_id=None,
    ):
        self.empresa = empresa
        self.fecha_inicio = self._convertir_fecha(fecha_inicio)
        self.fecha_fin = self._convertir_fecha(fecha_fin)
        self.departamento_id = departamento_id
        self.empleado_id = empleado_id

    @staticmethod
    def _convertir_fecha(valor):
        """
        Acepta una fecha de Python o una cadena YYYY-MM-DD.
        """
        if not valor:
            return None

        if isinstance(valor, str):
            return datetime.strptime(valor, "%Y-%m-%d").date()

        return valor

    def _obtener_empleados(self):
        empleados = Empleado.objects.filter(
            empresa=self.empresa,
            activo=True,
        ).select_related(
            "departamento",
            "turno",
        )

        if self.departamento_id:
            empleados = empleados.filter(
                departamento_id=self.departamento_id
            )

        if self.empleado_id:
            empleados = empleados.filter(
                id=self.empleado_id
            )

        return empleados.order_by("numero_empleado")

    def _obtener_asistencias(self):
        return Asistencia.objects.filter(
            empleado__empresa=self.empresa,
            fecha__range=(
                self.fecha_inicio,
                self.fecha_fin,
            ),
        ).select_related(
            "empleado",
            "empleado__departamento",
            "empleado__turno",
        ).order_by(
            "empleado__numero_empleado",
            "fecha",
        )

    def _obtener_incidencias(self):
        return IncidenciaDia.objects.filter(
            empleado__empresa=self.empresa,
            fecha__range=(
                self.fecha_inicio,
                self.fecha_fin,
            ),
        ).select_related(
            "empleado"
        ).order_by(
            "empleado__numero_empleado",
            "fecha",
        )

    def _obtener_movimientos(self):
        return Movimiento.objects.filter(
            asistencia__empleado__empresa=self.empresa,
            fecha__range=(
                self.fecha_inicio,
                self.fecha_fin,
            ),
        ).select_related(
            "asistencia",
            "asistencia__empleado",
        ).order_by(
            "asistencia__empleado__numero_empleado",
            "fecha",
            "hora",
        )

    def _obtener_tiempos_extra(self):
        return TiempoExtra.objects.filter(
            empleado__empresa=self.empresa,
            fecha__range=(
                self.fecha_inicio,
                self.fecha_fin,
            ),
        ).select_related(
            "empleado",
            "asistencia",
        ).order_by(
            "empleado__numero_empleado",
            "fecha",
        )
    
  

    def generar(self):
        if not self.fecha_inicio or not self.fecha_fin:
            return []
        
        dias_periodo = (
            self.fecha_fin - self.fecha_inicio
        ).days + 1

        empleados = list(self._obtener_empleados())
        empleados_ids = {empleado.id for empleado in empleados}

        asistencias = list(
            self._obtener_asistencias().filter(
                empleado_id__in=empleados_ids
            )
        )

        incidencias = list(
            self._obtener_incidencias().filter(
                empleado_id__in=empleados_ids
            )
        )

        movimientos = list(
            self._obtener_movimientos().filter(
                asistencia__empleado_id__in=empleados_ids
            )
        )

        tiempos_extra = list(
            self._obtener_tiempos_extra().filter(
                empleado_id__in=empleados_ids
            )
        )

        asistencias_por_empleado = defaultdict(list)
        incidencias_por_empleado = defaultdict(list)
        movimientos_por_empleado = defaultdict(list)
        movimientos_por_asistencia = defaultdict(list)   # ← NUEVA
        tiempos_extra_por_empleado = defaultdict(list)

        for asistencia in asistencias:
            asistencias_por_empleado[
                asistencia.empleado_id
            ].append(asistencia)

        for incidencia in incidencias:
            incidencias_por_empleado[
                incidencia.empleado_id
            ].append(incidencia)

        for movimiento in movimientos:

            movimientos_por_empleado[
                movimiento.asistencia.empleado_id
            ].append(movimiento)

            movimientos_por_asistencia[
                movimiento.asistencia_id
            ].append(movimiento)

        for tiempo_extra in tiempos_extra:
            tiempos_extra_por_empleado[
                tiempo_extra.empleado_id
            ].append(tiempo_extra)

        resultados = []

        for empleado in empleados:

            asistencias_empleado = asistencias_por_empleado[
                empleado.id
            ]

            incidencias_empleado = incidencias_por_empleado[
                empleado.id
            ]

            movimientos_empleado = movimientos_por_empleado[
                empleado.id
            ]

            tiempos_extra_empleado = tiempos_extra_por_empleado[
                empleado.id
            ]

            tiempo_extra = sum(
                registro.horas or 0
                for registro in tiempos_extra_empleado
            )

    # ==========================================================
    # ÍNDICES POR FECHA
    # ==========================================================
            asistencias_por_fecha = {
                asistencia.fecha: asistencia
                for asistencia in asistencias_empleado
            }

            incidencias_por_fecha = {
                incidencia.fecha: incidencia
                for incidencia in incidencias_empleado
            }

    # ==========================================================
    # CONTADORES DEL PERÍODO
    # ==========================================================
            dias_laborables_periodo = 0
            dias_laborados = 0
            faltas = 0
            retardos = 0

            vacaciones = 0
            incapacidades = 0
            descansos = 0
            permisos = 0

            incompletos = 0
            irregulares = 0
            pendientes = 0
            no_laborales = 0
            futuros = 0
            sin_turno = 0
            sin_control = 0

            salidas_permiso = 0
            horas_trabajadas = 0

            detalle_dias = []

    # No se evalúan como falta fechas posteriores a hoy.
            hoy = timezone.localdate()
            fecha_limite = min(
                self.fecha_fin,
                hoy,
            )

            fecha_actual = self.fecha_inicio

    # ==========================================================
    # MOTOR DIARIO ÚNICO
    # ==========================================================
            while fecha_actual <= fecha_limite:

                asistencia_dia = asistencias_por_fecha.get(
                    fecha_actual
                )

                incidencia_dia = incidencias_por_fecha.get(
                    fecha_actual
                )

                if asistencia_dia:
                    movimientos_dia = movimientos_por_asistencia[
                        asistencia_dia.id
                    ]
                else:
                    movimientos_dia = []

                calculadora = CalculadoraAsistencia(
                    empleado=empleado,
                    fecha=fecha_actual,
                    movimientos=movimientos_dia,
                    asistencia=asistencia_dia,
                    incidencia_dia=incidencia_dia,
                )

                resultado_dia = calculadora.calcular()
                detalle_dias.append(resultado_dia)

                estado = resultado_dia["estado"]

        # Día laboral según el motor.
                if resultado_dia["es_laborable"]:
                    dias_laborables_periodo += 1

        # Asistencia real.
                if resultado_dia["es_dia_laborado"]:
                    dias_laborados += 1

                if resultado_dia["es_retardo"]:
                    retardos += 1

                if resultado_dia["es_falta"]:
                    faltas += 1

        # Horas y permisos.
                horas_trabajadas += (
                    resultado_dia["horas_trabajadas"] or 0
                )

                salidas_permiso += (
                    resultado_dia["salidas_permiso"] or 0
                )

        # Incidencias laborales.
                if estado == "VACACIONES":
                    vacaciones += 1

                elif estado == "INCAPACIDAD":
                    incapacidades += 1

                elif estado == "DESCANSO":
                    descansos += 1

                elif estado == "PERMISO":
                    permisos += 1

        # Estados que requieren revisión.
                elif estado == "INCOMPLETO":
                    incompletos += 1

                elif estado == "IRREGULAR":
                    irregulares += 1

                elif estado == "PENDIENTE":
                    pendientes += 1

                elif estado == "NO_LABORAL":
                    no_laborales += 1

                elif estado == "FUTURO":
                    futuros += 1

                elif estado == "SIN_TURNO":
                    sin_turno += 1

                elif estado == "SIN_CONTROL":
                    sin_control += 1

                fecha_actual += timedelta(days=1)

            horas_trabajadas = round(
                horas_trabajadas,
                2,
            )

                # ==========================================================
            # TIEMPO EXTRA
            # ==========================================================
            # La fuente oficial es TiempoExtra, no Movimiento.
            tiempo_extra = 0

            for asistencia in asistencias_empleado:

                movimientos_dia = movimientos_por_asistencia.get(
                    asistencia.id,
                    []
                )

                inicio_extra = None
                fin_extra = None

                for movimiento in movimientos_dia:

                    if movimiento.tipo == "INICIO_TIEMPO_EXTRA":
                        inicio_extra = movimiento.hora

                    elif movimiento.tipo == "FIN_TIEMPO_EXTRA":
                        fin_extra = movimiento.hora

                if inicio_extra and fin_extra:

                    t_inicio = datetime.combine(
                        asistencia.fecha,
                        inicio_extra
                    )

                    t_fin = datetime.combine(
                        asistencia.fecha,
                        fin_extra
                    )

                    diff = t_fin - t_inicio

                    total_minutos = int(
                        diff.total_seconds() / 60
                    )

                    horas_base = total_minutos // 60
                    minutos = total_minutos % 60

                    if minutos >= 45:
                        horas_final = horas_base + 1
                    else:
                        horas_final = horas_base

                    tiempo_extra += horas_final

            # ==========================================================
            # TOTALES DE INCIDENCIAS
            # ==========================================================
            total_incidencias = (
                vacaciones
                + incapacidades
                + descansos
                + permisos
            )

            # ==========================================================
            # POLÍTICA PROVISIONAL DE DÍAS A PAGAR
            # ==========================================================
            dias_a_pagar = dias_laborados

            # ==========================================================
            # TOTAL DE FECHAS CLASIFICADAS
            # ==========================================================
            total_fila = (
                dias_laborados
                + faltas
                + vacaciones
                + incapacidades
                + descansos
                + permisos
                + incompletos
                + irregulares
                + pendientes
                + no_laborales
                + sin_turno
            )

            dias_evaluados = (
                fecha_limite - self.fecha_inicio
            ).days + 1

            diferencia = dias_evaluados - total_fila

            resultados.append({
                "empleado_obj": empleado,
                "numero_empleado": empleado.numero_empleado,
                "empleado": empleado.nombre,
                "departamento": (
                    empleado.departamento.nombre
                    if empleado.departamento
                    else "Sin departamento"
                ),
                "turno": (
                    empleado.turno.nombre
                    if empleado.turno
                    else "Sin turno"
                ),
                "control_horario": empleado.control_horario,

                "dias_periodo": dias_periodo,
                "dias_laborables": dias_laborables_periodo,
                "dias_laborados": dias_laborados,
                "dias_a_pagar": dias_a_pagar,
                "total_fila": total_fila,
                "diferencia": diferencia,

                "faltas": faltas,
                "retardos": retardos,
                "vacaciones": vacaciones,
                "incapacidades": incapacidades,
                "descansos": descansos,
                "permisos": permisos,
                "incidencias": total_incidencias,

                "salidas_permiso": salidas_permiso,
                "horas_trabajadas": horas_trabajadas,
                "tiempo_extra": tiempo_extra,

                "observaciones": "",

                "_asistencias": asistencias_empleado,
                "_incidencias": incidencias_empleado,
                "_movimientos": movimientos_empleado,
                "_tiempos_extra": tiempos_extra_empleado,
            })

        return resultados