from datetime import datetime, timedelta


class CalculadoraAsistencia:

    def __init__(self, empleado, fecha, movimientos):
        self.empleado = empleado
        self.fecha = fecha
        self.movimientos = list(movimientos)
        self.turno = getattr(empleado, "turno", None)

    # ========================
    # PROCESO PRINCIPAL
    # ========================
    def calcular(self):

        entrada = self._entrada()
        salida = self._salida()

        return {
            "entrada": entrada,
            "salida": salida,
            "retardo": self._retardo(),
            "horas_trabajadas": self._horas_trabajadas(),
            "estado": self._estado(entrada, salida),  # 👈 AQUÍ ESTÁ EL FIX
            "incidencias": self._incidencias(),
        }

    # ========================
    # ENTRADA
    # ========================
    def _entrada(self):
        for m in self.movimientos:
            if m.tipo.strip().upper() == "ENTRADA":
                return m.hora
        return None

    # ========================
    # SALIDA
    # ========================
    def _salida(self):
        for m in reversed(self.movimientos):
            if m.tipo.strip().upper() == "SALIDA":
                return m.hora
        return None

    # ========================
    # RETARDO
    # ========================
    def _retardo(self):
        if not self.turno:
            return False

        entrada = self._entrada()
        if not entrada:
            return False

        hora_turno = self.turno.hora_entrada
        tolerancia = timedelta(minutes=self.turno.tolerancia_minutos)

        hora_real = datetime.combine(self.fecha, entrada)
        hora_base = datetime.combine(self.fecha, hora_turno)

        return hora_real > (hora_base + tolerancia)

    # ========================
    # HORAS TRABAJADAS (CON PERMISOS)
    # ========================
    def _horas_trabajadas(self):
        entrada = self._entrada()
        salida = self._salida()

        if not entrada or not salida:
            return 0

        h1 = datetime.combine(self.fecha, entrada)
        h2 = datetime.combine(self.fecha, salida)

        total = (h2 - h1).total_seconds()

        # =========================
        # DESCONTAR PERMISOS
        # =========================
        tiempo_permiso = 0
        salida_permiso = None

        for m in self.movimientos:
            tipo = m.tipo.strip().upper()

            if tipo == "SALIDA_PERMISO":
                salida_permiso = datetime.combine(self.fecha, m.hora)

            elif tipo == "REGRESO" and salida_permiso:
                regreso = datetime.combine(self.fecha, m.hora)
                tiempo_permiso += (regreso - salida_permiso).total_seconds()
                salida_permiso = None

        total_real = total - tiempo_permiso

        return round(total_real / 3600, 2)

    # ========================
    # ESTADO
    # ========================
    def _estado(self, entrada, salida):

        if not entrada and not salida:
            return "FALTA"

        if entrada and not salida:
            return "INCOMPLETO"

        if not entrada and salida:
            return "IRREGULAR"

        return "ASISTENCIA"
    
    def _incidencias(self):
        incidencias = []
        salida_permiso_abierta = False
        contador_sin_regreso = 0

        for m in self.movimientos:
            tipo = m.tipo.strip().upper()

            if tipo == "SALIDA_PERMISO":
                if salida_permiso_abierta:
                    contador_sin_regreso += 1
                else:
                    salida_permiso_abierta = True

            elif tipo == "REGRESO":
                salida_permiso_abierta = False

        if contador_sin_regreso > 0:
            incidencias.append("MULTIPLES SALIDAS DE PERMISO SIN REGRESO")

        if salida_permiso_abierta:
            incidencias.append("PERMISO SIN REGRESO FINAL")

        return incidencias
    
    def guardar_incidencias(self):
        from core.models import Incidencia

        incidencias = self._incidencias()

        # 1. Eliminar incidencias previas del día
        Incidencia.objects.filter(
            empleado=self.empleado,
            fecha_inicio=self.fecha,
            fecha_fin=self.fecha
        ).delete()

        # 2. Crear nuevas incidencias
        for tipo in incidencias:
            Incidencia.objects.create(
                empleado=self.empleado,
                tipo=tipo,
                fecha_inicio=self.fecha,
                fecha_fin=self.fecha,
            )