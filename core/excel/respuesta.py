from django.http import HttpResponse


def crear_respuesta_excel(
    workbook,
    nombre_archivo,
):
    """
    Crea la respuesta HTTP estándar para descargar un archivo Excel.
    """

    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{nombre_archivo}"'
    )

    workbook.save(response)

    return response