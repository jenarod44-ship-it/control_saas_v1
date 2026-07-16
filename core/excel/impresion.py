from openpyxl.worksheet.page import PageMargins


def configurar_impresion(
    ws,
    fila_encabezado,
    ultima_columna,
    ultima_fila,
):
    """
    Aplica la configuración estándar de navegación e impresión.
    """

    ws.freeze_panes = f"A{fila_encabezado + 1}"

    if ultima_fila > fila_encabezado:
        ws.auto_filter.ref = (
            f"A{fila_encabezado}:"
            f"{ultima_columna}{ultima_fila}"
        )

    ws.sheet_view.showGridLines = False

    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.print_title_rows = (
        f"{fila_encabezado}:{fila_encabezado}"
    )

    ws.print_area = (
        f"A1:{ultima_columna}{ultima_fila}"
    )

    ws.page_margins = PageMargins(
        left=0.25,
        right=0.25,
        top=0.50,
        bottom=0.50,
        header=0.20,
        footer=0.20,
    )