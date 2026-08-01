from datetime import datetime, timedelta

from django.utils import timezone

from core.models import IncidenciaDia
from core.utils.laboral import es_dia_laboral


class CalculadoraAsistencia:
    """
    Motor único para clasificar un día de un empleado.

    Esta clase:
    - Lee datos.
    - Calcula un resultado diario.
    - No crea, modifica ni elimina registros.
    """

    def __init__(
        self,
        empleado,
        fecha,
        movimientos=None,
        asistencia=None,
        incidencia_dia=None,
    ):
        self.empleado = empleado
        self.fecha = fecha
        self.movimientos = list(movimientos or [])
        self.asistencia = asistencia
        self.turno = getattr(empleado, "turno", None)

        # Permite recibir la incidencia precargada para evitar
        # consultas repetidas en reportes grandes.
        self.incidencia_dia = incidencia_dia

    # ==========================================================
    # PROCESO PRINCIPAL
    # ==========================================================
    def calcular(self):
        entrada = self._entrada()
        salida = self._salida()
        incidencia = self._obtener_incidencia()
        es_laborable = self._es_laborable()
        retardo = self._es_retardo(entrada)
        horas_trabajadas = self._horas_trabajadas(
            entrada,
            salida,
        )
        alertas = self._obtener_alertas(
            entrada,
            salida,
        )

        estado, motivo = self._determinar_estado(
            entrada=entrada,
            salida=salida,
            incidencia=incidencia,
            es_laborable=es_laborable,
            retardo=retardo,
        )

        return {
            # Identificación
            "empleado": self.empleado,
            "fecha": self.fecha,

            # Configuración laboral
            "control_horario": self.empleado.control_horario,
            "turno": self.turno,
            "es_laborable": es_laborable,

            # Registro de asistencia
            "asistencia": self.asistencia,
            "entrada": entrada,
            "salida": salida,

            # Resultado principal
            "estado": estado,
            "motivo": motivo,

            # Banderas para reportes
            "es_asistencia": estado in {
                "OK",
                "RETARDO",
                "INCOMPLETO",
            },
            "es_dia_laborado": (
                es_laborable
                and estado in ["OK", "RETARDO", "SIN_CONTROL"]
            ),
            
            "es_retardo": estado == "RETARDO",
            "es_falta": estado == "FALTA",
            "es_incompleto": estado == "INCOMPLETO",
            "es_irregular": estado == "IRREGULAR",
            "es_pendiente": estado == "PENDIENTE",

            # Incidencia laboral
            "incidencia": incidencia,
            "tipo_incidencia": (
                incidencia.tipo
                if incidencia
                else None
            ),

            # Tiempo
            "horas_trabajadas": horas_trabajadas,

            # Permisos y anomalías
            "salidas_permiso": self._contar_salidas_permiso(),
            "permiso_abierto": self._permiso_abierto(),
            "alertas": alertas,
        }

    # ==========================================================
    # DATOS BÁSICOS
    # ==========================================================
    def _entrada(self):
        if self.asistencia:
            return self.asistencia.hora_entrada

        # Compatibilidad temporal con registros antiguos.
        for movimiento in self.movimientos:
            tipo = self._tipo_movimiento(movimiento)

            if tipo == "ENTRADA":
                return movimiento.hora

        return None

    def _salida(self):
        if self.asistencia:
            return self.asistencia.hora_salida

        # Compatibilidad temporal con registros antiguos.
        for movimiento in reversed(self.movimientos):
            tipo = self._tipo_movimiento(movimiento)

            if tipo == "SALIDA":
                return movimiento.hora

        return None

    def _obtener_incidencia(self):
        if self.incidencia_dia is not None:
            return self.incidencia_dia

        return (
            IncidenciaDia.objects
            .filter(
                empleado=self.empleado,
                fecha=self.fecha,
            )
            .select_related("incidencia")
            .first()
        )

    def _es_laborable(self):
        return es_dia_laboral(
            self.empleado,
            self.fecha,
        )

        return es_dia_laboral(
            self.empleado,
            self.fecha,
        )

    # ==========================================================
    # ESTADO DEL DÍA
    # ==========================================================
    def _determinar_estado(
        self,
        entrada,
        salida,
        incidencia,
        es_laborable,
        retardo,
    ):
        # 1. Una incidencia registrada tiene prioridad.
        if incidencia:
            return (
                incidencia.tipo,
                f"Incidencia registrada: {incidencia.tipo}.",
            )

        # 2. Fechas futuras.
        hoy = timezone.localdate()

        if self.fecha > hoy:
            return (
                "FUTURO",
                "La fecha todavía no ocurre.",
            )

        # ==========================================================
        # EMPLEADO SIN CONTROL DE HORARIO
        # ==========================================================
        # Debe registrar asistencia, pero no se evalúan
        # días laborales, turno, tolerancia ni puntualidad.
        if not self.empleado.control_horario:

            # Sin ninguna checada.
            if not entrada and not salida:
                return (
                    "FALTA",
                    "No existe registro de asistencia.",
                )

            # Entrada sin salida.
            if entrada and not salida:
                return (
                    "INCOMPLETO",
                    "Existe entrada, pero no existe salida.",
                )

            # Salida sin entrada.
            if not entrada and salida:
                return (
                    "IRREGULAR",
                    "Existe salida, pero no existe entrada.",
                )

            # Entrada y salida completas.
            return (
                "OK",
                "Asistencia completa. No se evalúa puntualidad.",
            )

        # ==========================================================
        # EMPLEADO CON CONTROL DE HORARIO
        # ==========================================================

        # 3. Día no laborable.
        if not es_laborable:
            return (
                "NO_LABORAL",
                "La fecha no corresponde a un día laboral.",
            )

        # 4. Empleado sin turno.
        if not self.turno:
            return (
                "SIN_TURNO",
                "El empleado no tiene un turno asignado.",
            )

        # 5. No existe ninguna checada.
        if not entrada and not salida:
            if self._todavia_puede_entrar():
                return (
                    "PENDIENTE",
                    "La hora límite de entrada todavía no ha pasado.",
                )

            return (
                "FALTA",
                "Era día laborable y no existe registro de entrada.",
            )
        
    # 6. Entrada sin salida.
        if entrada and not salida:
            return (
                "INCOMPLETO",
                "Existe entrada, pero no existe salida.",
            )

    # 7. Salida sin entrada.
        if not entrada and salida:
            return (
                "IRREGULAR",
                "Existe salida, pero no existe entrada.",
            )

    # 8. Asistencia completa con retardo.
        if retardo:
            return (
                "RETARDO",
                "La entrada fue posterior a la tolerancia del turno.",
            )

    # 9. Asistencia completa y puntual.
        return (
            "OK",
            "La asistencia está completa y dentro del horario permitido.",
        )

    def _todavia_puede_entrar(self):
        hoy = timezone.localdate()

        if self.fecha != hoy:
            return False

        if not self.turno:
            return False

        limite_entrada = (
            datetime.combine(
                self.fecha,
                self.turno.hora_entrada,
            )
            + timedelta(
                minutes=self.turno.tolerancia_minutos
            )
        ).time()

        hora_actual = timezone.localtime().time()

        return hora_actual <= limite_entrada

    # ==========================================================
    # RETARDO
    # ==========================================================
    def _es_retardo(self, entrada):
        if not self.turno or not entrada:
            return False

        hora_real = datetime.combine(
            self.fecha,
            entrada,
        )

        hora_limite = (
            datetime.combine(
                self.fecha,
                self.turno.hora_entrada,
            )
            + timedelta(
                minutes=self.turno.tolerancia_minutos
            )
        )

        return hora_real > hora_limite

    # ==========================================================
    # HORAS TRABAJADAS
    # ==========================================================
    def _horas_trabajadas(
        self,
        entrada,
        salida,
    ):
        if not entrada or not salida:
            return 0

        fecha_hora_entrada = datetime.combine(
            self.fecha,
            entrada,
        )

        fecha_hora_salida = datetime.combine(
            self.fecha,
            salida,
        )

        # Permite turnos que terminan al día siguiente.
        if fecha_hora_salida < fecha_hora_entrada:
            fecha_hora_salida += timedelta(days=1)

        segundos_totales = (
            fecha_hora_salida
            - fecha_hora_entrada
        ).total_seconds()

        segundos_permiso = self._segundos_permiso()

        segundos_reales = max(
            segundos_totales - segundos_permiso,
            0,
        )

        return round(
            segundos_reales / 3600,
            2,
        )

    def _segundos_permiso(self):
        segundos = 0
        salida_permiso = None

        movimientos_ordenados = sorted(
            self.movimientos,
            key=lambda movimiento: movimiento.hora,
        )

        for movimiento in movimientos_ordenados:
            tipo = self._tipo_movimiento(movimiento)

            if tipo == "SALIDA_PERMISO":
                # Si ya existe una salida abierta, no reemplazamos
                # el inicio anterior con un dato inconsistente.
                if salida_permiso is None:
                    salida_permiso = datetime.combine(
                        self.fecha,
                        movimiento.hora,
                    )

            elif tipo == "REGRESO" and salida_permiso:
                regreso = datetime.combine(
                    self.fecha,
                    movimiento.hora,
                )

                if regreso < salida_permiso:
                    regreso += timedelta(days=1)

                segundos += max(
                    (regreso - salida_permiso).total_seconds(),
                    0,
                )

                salida_permiso = None

        return segundos

    # ==========================================================
    # PERMISOS
    # ==========================================================
    def _contar_salidas_permiso(self):
        return sum(
            1
            for movimiento in self.movimientos
            if self._tipo_movimiento(movimiento)
            == "SALIDA_PERMISO"
        )

    def _permiso_abierto(self):
        permiso_abierto = False

        movimientos_ordenados = sorted(
            self.movimientos,
            key=lambda movimiento: movimiento.hora,
        )

        for movimiento in movimientos_ordenados:
            tipo = self._tipo_movimiento(movimiento)

            if tipo == "SALIDA_PERMISO":
                permiso_abierto = True

            elif tipo == "REGRESO":
                permiso_abierto = False

        return permiso_abierto

    # ==========================================================
    # ALERTAS DE INTEGRIDAD
    # ==========================================================
    def _obtener_alertas(
        self,
        entrada,
        salida,
    ):
        alertas = []
        permiso_abierto = False

        movimientos_ordenados = sorted(
            self.movimientos,
            key=lambda movimiento: movimiento.hora,
        )

        for movimiento in movimientos_ordenados:
            tipo = self._tipo_movimiento(movimiento)

            if tipo == "SALIDA_PERMISO":
                if permiso_abierto:
                    alertas.append(
                        "MÚLTIPLES SALIDAS DE PERMISO SIN REGRESO"
                    )
                else:
                    permiso_abierto = True

            elif tipo == "REGRESO":
                if not permiso_abierto:
                    alertas.append(
                        "REGRESO SIN SALIDA DE PERMISO"
                    )
                else:
                    permiso_abierto = False

        if permiso_abierto:
            alertas.append(
                "PERMISO SIN REGRESO FINAL"
            )

        if not entrada and salida:
            alertas.append(
                "SALIDA SIN ENTRADA"
            )

        return alertas

    # ==========================================================
    # UTILIDADES
    # ==========================================================
    @staticmethod
    def _tipo_movimiento(movimiento):
        return (
            movimiento.tipo
            .strip()
            .upper()
        )