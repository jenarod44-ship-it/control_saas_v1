from collections import defaultdict
from datetime import datetime, timedelta
from asistencia.models import Asistencia, Movimiento, TiempoExtra
from core.models import IncidenciaDia
from nucleo.models import Empleado
from django.utils import timezone
from core.calculadora import CalculadoraAsistencia
from core.utils.laboral import es_dia_laboral


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

            faltas = 0

    # ==========================
    # SALIDAS CON PERMISO
    # ==========================

            salidas_permiso = sum(
                1
                for movimiento in movimientos_empleado
                if movimiento.tipo == "SALIDA_PERMISO"
            )

    # ==========================
    # HORAS TRABAJADAS
    # ==========================

            horas_trabajadas = 0

            for asistencia in asistencias_empleado:

                movimientos_asistencia = movimientos_por_asistencia[
                    asistencia.id
                ]

                calculadora = CalculadoraAsistencia(
                    empleado,
                    asistencia.fecha,
                    movimientos_asistencia,
                )

                resultado = calculadora.calcular()
                horas = resultado.get("horas_trabajadas")

                if isinstance(horas, (int, float)):
                    horas_trabajadas += horas

            horas_trabajadas = round(horas_trabajadas, 2)

    # ==========================
    # TIEMPO EXTRA
    # ==========================

            tiempo_extra = 0

            for asistencia in asistencias_empleado:

                movimientos_asistencia = movimientos_por_asistencia[
                    asistencia.id
                ]

                inicio_extra = None
                fin_extra = None

                for movimiento in movimientos_asistencia:

                    if movimiento.tipo == "INICIO_TIEMPO_EXTRA":
                        inicio_extra = movimiento.hora

                    elif movimiento.tipo == "FIN_TIEMPO_EXTRA":
                        fin_extra = movimiento.hora

                if not inicio_extra or not fin_extra:
                    continue

                fecha_hora_inicio = datetime.combine(
                    asistencia.fecha,
                    inicio_extra,
                )

                fecha_hora_fin = datetime.combine(
                    asistencia.fecha,
                    fin_extra,
                )

                total_minutos = int(
                    (
                        fecha_hora_fin
                        - fecha_hora_inicio
                    ).total_seconds() / 60
                )

                horas_base = total_minutos // 60
                minutos_restantes = total_minutos % 60

                if minutos_restantes >= 45:
                    horas_base += 1

                tiempo_extra += horas_base

            asistencias_por_fecha = {
                asistencia.fecha: asistencia
                for asistencia in asistencias_empleado
            }

            fechas_con_incidencia = {
                incidencia.fecha
                for incidencia in incidencias_empleado
            }

            hoy = timezone.localdate()
            fecha_limite = min(self.fecha_fin, hoy)
            fecha_actual = self.fecha_inicio

            if empleado.control_horario and empleado.turno:

                while fecha_actual <= fecha_limite:

                    if not es_dia_laboral(empleado, fecha_actual):
                        fecha_actual += timedelta(days=1)
                        continue

                    if fecha_actual in fechas_con_incidencia:
                        fecha_actual += timedelta(days=1)
                        continue

                    asistencia_dia = asistencias_por_fecha.get(fecha_actual)

                    if asistencia_dia and asistencia_dia.hora_entrada:
                        fecha_actual += timedelta(days=1)
                        continue

                    if fecha_actual == hoy:
                        limite_entrada = (
                            datetime.combine(
                                fecha_actual,
                                empleado.turno.hora_entrada,
                            )
                            + timedelta(
                                minutes=empleado.turno.tolerancia_minutos
                            )
                        ).time()

                        if timezone.localtime().time() <= limite_entrada:
                            fecha_actual += timedelta(days=1)
                            continue

                    faltas += 1
                    fecha_actual += timedelta(days=1)

            dias_laborados = sum(
                1
                for asistencia in asistencias_empleado
                if asistencia.hora_entrada
            )

            retardos = 0

            if empleado.control_horario and empleado.turno:
                for asistencia in asistencias_empleado:
                    if not asistencia.hora_entrada:
                        continue

                    limite_entrada = (
                        datetime.combine(
                            asistencia.fecha,
                            empleado.turno.hora_entrada,
                        )
                        + timedelta(
                            minutes=empleado.turno.tolerancia_minutos
                        )
                    ).time()

                    if asistencia.hora_entrada > limite_entrada:
                        retardos += 1

            vacaciones = sum(
                1
                for incidencia in incidencias_empleado
                if incidencia.tipo == "VACACIONES"
            )

            incapacidades = sum(
                1
                for incidencia in incidencias_empleado
                if incidencia.tipo == "INCAPACIDAD"
            )

            descansos = sum(
                1
                for incidencia in incidencias_empleado
                if incidencia.tipo == "DESCANSO"
            )

            permisos = sum(
                1
                for incidencia in incidencias_empleado
                if incidencia.tipo == "PERMISO"
            )

            total_incidencias = (
                vacaciones
                + incapacidades
                + descansos
                + permisos
            )

            

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
                "dias_laborados": dias_laborados,
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
                "_movimientos": movimientos_por_empleado[
                    empleado.id
                ],
                "_tiempos_extra": tiempos_extra_por_empleado[
                    empleado.id
                ],
            })

        return resultados