"""
Utilidades para importación de trámites desde Excel
"""
import openpyxl
from decimal import Decimal, InvalidOperation
from .models import TipoVehiculo, Taller, ConfiguracionTaller


def convertir_a_decimal(valor):
    """
    Convierte un valor del Excel a Decimal, manejando None y diferentes tipos
    """
    if valor is None or valor == '':
        return None

    try:
        # Si ya es número, convertir directamente
        if isinstance(valor, (int, float)):
            return Decimal(str(valor))
        # Si es string, limpiar y convertir
        valor_str = str(valor).replace(',', '').replace('$', '').strip()
        if valor_str:
            return Decimal(valor_str)
        return None
    except (ValueError, InvalidOperation):
        return None


def importar_tramites_desde_excel(archivo_path):
    """
    Importa trámites desde un archivo Excel con la estructura:
    Columna 1: CODIGO TARIFA (número)
    Columna 2: TARIFA (nombre del trámite)
    Columna 3: PROVINCIAL (precio provincial)
    Columna 4: NACIONAL (precio nacional)
    Columna 5: CAJUTAC (precio cajutac)

    Returns:
        tuple: (cantidad_creados, cantidad_errores, lista_errores)
    """
    try:
        wb = openpyxl.load_workbook(archivo_path)
        ws = wb.active

        creados = 0
        errores = 0
        lista_errores = []

        # IMPORTANTE: Borrar todos los trámites existentes
        TipoVehiculo.objects.all().delete()
        print("Trámites existentes eliminados")

        # Empezar desde la fila 2 (la fila 1 son encabezados)
        for i, row in enumerate(ws.iter_rows(min_row=2), start=2):
            # Obtener valores de las celdas
            codigo = row[0].value
            nombre = row[1].value if len(row) > 1 else None
            precio_prov = row[2].value if len(row) > 2 else None
            precio_nac = row[3].value if len(row) > 3 else None
            precio_caj = row[4].value if len(row) > 4 else None

            # Si la fila está completamente vacía, omitir
            if all(v is None for v in [codigo, nombre, precio_prov, precio_nac, precio_caj]):
                continue

            # Validar que al menos tengamos nombre
            if not nombre or str(nombre).strip() == '':
                errores += 1
                lista_errores.append(f"Fila {i}: Falta nombre del trámite")
                continue

            try:
                # Formatear código de trámite
                if codigo is not None:
                    codigo_str = f"TRM-{int(codigo):03d}"  # TRM-001, TRM-002, etc.
                else:
                    codigo_str = f"TRM-{i-1:03d}"  # Usar número de fila si no hay código

                # Convertir precios a Decimal
                precio_provincial_dec = convertir_a_decimal(precio_prov)
                precio_nacional_dec = convertir_a_decimal(precio_nac)
                precio_cajutad_dec = convertir_a_decimal(precio_caj)

                # Crear el trámite
                tramite = TipoVehiculo.objects.create(
                    codigo_tramite=codigo_str,
                    nombre=str(nombre).strip(),
                    precio_provincial=precio_provincial_dec,
                    precio_nacional=precio_nacional_dec,
                    precio_cajutad=precio_cajutad_dec,
                    duracion_minutos=30,  # Valor por defecto
                    status=True  # Activo por defecto
                )

                creados += 1
                print(f"Creado: {tramite}")

            except Exception as e:
                errores += 1
                lista_errores.append(f"Fila {i}: Error al crear trámite - {str(e)}")
                continue

        wb.close()
        return (creados, errores, lista_errores)

    except FileNotFoundError:
        return (0, 1, ["Archivo no encontrado"])
    except Exception as e:
        return (0, 1, [f"Error al procesar Excel: {str(e)}"])


def crear_configuraciones_taller():
    """
    Crea ConfiguracionTaller para todas las combinaciones de Taller × TipoVehiculo
    Solo crea las que no existen. Mantiene las existentes.

    Returns:
        int: Cantidad de configuraciones creadas
    """
    talleres = Taller.objects.filter(status=True)
    tipos_vehiculo = TipoVehiculo.objects.filter(status=True)

    creadas = 0

    for taller in talleres:
        for tipo_vehiculo in tipos_vehiculo:
            # Crear solo si no existe
            config, created = ConfiguracionTaller.objects.get_or_create(
                taller=taller,
                tipo_vehiculo=tipo_vehiculo,
                defaults={
                    'turnos_simultaneos': 2,
                    'intervalo_minutos': 30,
                    'status': True
                }
            )
            if created:
                creadas += 1
                print(f"Configuración creada: {taller.get_nombre()} - {tipo_vehiculo.nombre}")

    return creadas
