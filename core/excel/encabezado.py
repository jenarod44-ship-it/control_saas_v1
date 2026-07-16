from django.utils import timezone

from .estilos import (
    ALINEACION_CENTRO,
    ALINEACION_IZQUIERDA,
    BORDE_FINO,
    FUENTE_ENCABEZADO,
    FUENTE_GENERADO,
    FUENTE_NEGRITA,
    FUENTE_TITULO,
    RELLENO_TITULO,
)

from core.excel.estilos import (
    ALINEACION_CENTRO,
    ALINEACION_IZQUIERDA,
    FUENTE_GENERADO,
    FUENTE_NEGRITA,
    FUENTE_TITULO,
    RELLENO_TITULO,
)


def escribir_encabezado_reporte(
    ws,
    titulo,
    empresa,
    inicio=None,
    fin=None,
    ultima_columna="G",
):
    
    def escribir_encabezados(ws, fila, encabezados):

        for columna, texto in enumerate(encabezados, start=1):
            celda = ws.cell(
                row=fila,
                column=columna,
                value=texto,
            )

            celda.font = FUENTE_ENCABEZADO
            celda.fill = RELLENO_TITULO
            celda.alignment = ALINEACION_CENTRO
            celda.border = BORDE_FINO
    """
    Escribe el encabezado estándar de los reportes Excel.

    Filas:
    1 - Título
    2 - Empresa
    3 - Periodo
    4 - Fecha y hora de generación
    """

    ws.merge_cells(f"A1:{ultima_columna}1")
    ws["A1"] = titulo
    ws["A1"].font = FUENTE_TITULO
    ws["A1"].fill = RELLENO_TITULO
    ws["A1"].alignment = ALINEACION_CENTRO
    ws.row_dimensions[1].height = 26

    ws.merge_cells(f"A2:{ultima_columna}2")
    ws["A2"] = f"Empresa: {empresa.nombre if empresa else ''}"
    ws["A2"].font = FUENTE_NEGRITA
    ws["A2"].alignment = ALINEACION_IZQUIERDA

    if inicio and fin:
        periodo = f"Periodo: {inicio} a {fin}"
    elif inicio:
        periodo = f"Desde: {inicio}"
    elif fin:
        periodo = f"Hasta: {fin}"
    else:
        periodo = "Periodo: Todos"

    ws.merge_cells(f"A3:{ultima_columna}3")
    ws["A3"] = periodo
    ws["A3"].alignment = ALINEACION_IZQUIERDA

    generado = timezone.localtime().strftime("%d/%m/%Y %H:%M")

    ws.merge_cells(f"A4:{ultima_columna}4")
    ws["A4"] = f"Generado: {generado}"
    ws["A4"].font = FUENTE_GENERADO
    ws["A4"].alignment = ALINEACION_IZQUIERDA

   


def escribir_encabezados(ws, fila, encabezados):

    for columna, texto in enumerate(encabezados, start=1):

        celda = ws.cell(
            row=fila,
            column=columna,
            value=texto,
        )

        celda.font = FUENTE_ENCABEZADO
        celda.fill = RELLENO_TITULO
        celda.alignment = ALINEACION_CENTRO
        celda.border = BORDE_FINO