import pandas as pd
from django.utils.safestring import mark_safe

def excel_to_html(file_path):
    try:
        df = pd.read_excel(file_path)
        # Reemplazar NaN/null por string vacío
        df = df.fillna("")
        # Generar tabla con clases Bootstrap y encabezados en negrita
        html = df.to_html(
            classes="table table-hover excel-table-responsive",
            index=False,
            border=0,
            justify='center',
            escape=False
        )
        # Solo devuelve la tabla, sin scripts ni links
        return mark_safe(html)
    except Exception as e:
        return f"<p>Error al procesar el archivo: {e}</p>"
