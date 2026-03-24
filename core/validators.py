# ==============================================================
# Validadores de archivos para uploads seguros
# ==============================================================

from django.core.exceptions import ValidationError


# Tipos MIME permitidos por categoría
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/ogg']
ALLOWED_DOC_TYPES = ['application/pdf', 'text/plain', 'application/msword',
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
ALLOWED_EXCEL_TYPES = ['application/vnd.ms-excel',
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']

# Tamaño máximo por categoría (en bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024       # 5 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024      # 50 MB
MAX_DOC_SIZE = 10 * 1024 * 1024        # 10 MB


def validar_archivo(archivo, categoria='image'):
    """
    Valida tipo MIME y tamaño de un archivo subido.

    Args:
        archivo: InMemoryUploadedFile o TemporaryUploadedFile
        categoria: 'image', 'video', 'document', 'excel'

    Returns:
        True si es válido

    Raises:
        ValidationError si no es válido
    """
    if not archivo:
        return True

    config = {
        'image': (ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, 'imagen'),
        'video': (ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE, 'video'),
        'document': (ALLOWED_DOC_TYPES, MAX_DOC_SIZE, 'documento'),
        'excel': (ALLOWED_EXCEL_TYPES, MAX_DOC_SIZE, 'Excel'),
    }

    allowed_types, max_size, label = config.get(categoria, config['document'])

    # Validar tipo MIME
    content_type = getattr(archivo, 'content_type', '')
    if content_type not in allowed_types:
        tipos_legibles = ', '.join([t.split('/')[-1].upper() for t in allowed_types])
        raise ValidationError(
            f'Tipo de archivo no permitido para {label}. '
            f'Tipos aceptados: {tipos_legibles}'
        )

    # Validar tamaño
    if archivo.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(
            f'El archivo es demasiado grande. '
            f'Tamaño máximo para {label}: {max_mb:.0f} MB'
        )

    return True


def validar_upload_seguro(request_files, campo, categoria='image'):
    """
    Helper para validar un upload desde request.FILES.
    Retorna (archivo, error_msg) - si error_msg es None, el archivo es válido.
    """
    archivo = request_files.get(campo)
    if not archivo:
        return None, None

    try:
        validar_archivo(archivo, categoria)
        return archivo, None
    except ValidationError as e:
        return None, str(e.message)
