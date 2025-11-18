import pandas as pd
from django.utils.safestring import mark_safe

def excel_to_list(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.fillna("")
        # Limpiar nombres de columna: si es 'Unnamed: X' y toda la columna está vacía, eliminarla
        clean_columns = {}
        for col in df.columns:
            if str(col).startswith('Unnamed'):
                # Si toda la columna está vacía, no la incluimos
                if df[col].replace("", pd.NA).isna().all():
                    continue
                # Si no, renombramos a string vacío
                clean_columns[col] = ''
            else:
                clean_columns[col] = col
        df.rename(columns=clean_columns, inplace=True)
        # Eliminar columnas con nombre vacío
        df = df.loc[:, df.columns != '']
        # Formatear todos los campos numéricos como moneda
        import re
        def limpiar_y_formatear(val):
            if isinstance(val, str):
                # Eliminar símbolo de pesos, espacios y puntos de miles
                val_limpio = val.replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
                # Si es vacío, devolver tal cual
                if not val_limpio.strip():
                    return val
                # Si es numérico, formatear
                try:
                    num = float(val_limpio)
                    return f"${num:,.2f}".replace(",", ".").replace(".", ",", 1)
                except ValueError:
                    return val
            elif isinstance(val, (int, float)):
                return f"${val:,.2f}".replace(",", ".").replace(".", ",", 1)
            return val
        # Aplicar a todas las columnas excepto la primera (descriptiva)
        for col in df.columns[1:]:
            df[col] = df[col].apply(limpiar_y_formatear)
        return df.to_dict(orient='records')
    except Exception as e:
        return []

def excel_to_html(file_path):
    try:
        df = pd.read_excel(file_path)
        # Reemplazar NaN/null por string vacío
        df = df.fillna("")
        # Formatear todos los campos numéricos como moneda
        import re
        def limpiar_y_formatear(val):
            if isinstance(val, str):
                val_limpio = val.replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
                if not val_limpio.strip():
                    return val
                try:
                    num = float(val_limpio)
                    return f"${num:,.2f}".replace(",", ".").replace(".", ",", 1)
                except ValueError:
                    return val
            elif isinstance(val, (int, float)):
                return f"${val:,.2f}".replace(",", ".").replace(".", ",", 1)
            return val
        for col in df.columns[1:]:
            df[col] = df[col].apply(limpiar_y_formatear)
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
