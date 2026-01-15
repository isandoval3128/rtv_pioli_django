"""
Utilidades para el módulo de turnos.
Incluye funciones para envío de emails con formato HTML profesional.
"""
import base64
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.models import EmailConfig


def get_email_connection():
    """
    Obtiene la conexión SMTP configurada en EmailConfig.
    Retorna None si no hay configuración.
    """
    email_config = EmailConfig.objects.first()
    if not email_config:
        return None, None

    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=email_config.email_host,
        port=email_config.email_port,
        username=email_config.email_host_user,
        password=email_config.email_host_password,
        use_tls=email_config.email_use_tls,
    )

    return connection, email_config


def get_qr_image_data(turno):
    """
    Obtiene los datos binarios del código QR del turno.
    Retorna None si no hay QR.
    """
    if not turno.qr_code:
        return None

    try:
        with turno.qr_code.open('rb') as qr_file:
            return qr_file.read()
    except Exception:
        return None


def format_fecha_legible(fecha):
    """
    Formatea una fecha en formato legible en español.
    Ej: "Lunes, 15 de enero de 2025"
    """
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    return f"{dias_semana[fecha.weekday()]}, {fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"


def generar_html_email_turno(turno, incluir_qr=False):
    """
    Genera el contenido HTML del email de confirmación de turno.
    Diseño profesional con colores del sistema (#13304D).

    Args:
        turno: Instancia del modelo Turno
        incluir_qr: Si True, incluye referencia a imagen QR con cid:qr_code
    """
    fecha_formateada = format_fecha_legible(turno.fecha)

    # Colores del sistema
    color_primario = "#13304D"
    color_secundario = "#1a4a73"
    color_fondo = "#f8f9fa"
    color_borde = "#e9ecef"

    # Sección QR con Content-ID reference
    qr_section = ""
    if incluir_qr:
        qr_section = f'''
                    <!-- QR Code -->
                    <tr>
                        <td style="padding: 0 40px 25px 40px; text-align: center;">
                            <p style="margin: 0 0 15px 0; color: {color_primario}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                Código QR
                            </p>
                            <img src="cid:qr_code" alt="Código QR del turno" style="width: 150px; height: 150px; border: 3px solid {color_primario}; border-radius: 10px; padding: 10px; background-color: white;">
                            <p style="margin: 10px 0 0 0; color: #6c757d; font-size: 12px;">
                                Presente este código al llegar al taller
                            </p>
                        </td>
                    </tr>
'''

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmación de Turno - {turno.codigo}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {color_fondo};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {color_primario} 0%, {color_secundario} 100%); padding: 30px 40px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">
                                Confirmación de Turno
                            </h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                Revisión Técnica Vehicular
                            </p>
                        </td>
                    </tr>

                    <!-- Código de turno destacado -->
                    <tr>
                        <td style="padding: 30px 40px 20px 40px; text-align: center;">
                            <div style="display: inline-block; background-color: {color_primario}; color: #ffffff; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 2px;">
                                {turno.codigo}
                            </div>
                            <p style="margin: 15px 0 0 0; color: #6c757d; font-size: 14px;">
                                Código de turno - Preséntelo al llegar
                            </p>
                        </td>
                    </tr>

                    <!-- Saludo -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <p style="margin: 0; color: #333333; font-size: 16px; line-height: 1.6;">
                                Estimado/a <strong>{turno.cliente.nombre} {turno.cliente.apellido}</strong>,
                            </p>
                            <p style="margin: 15px 0 0 0; color: #333333; font-size: 16px; line-height: 1.6;">
                                Su turno ha sido registrado exitosamente. A continuación encontrará los detalles:
                            </p>
                        </td>
                    </tr>

                    <!-- Fecha y hora destacada -->
                    <tr>
                        <td style="padding: 0 40px 25px 40px;">
                            <table role="presentation" style="width: 100%; background-color: {color_fondo}; border-radius: 10px; border: 2px solid {color_primario};">
                                <tr>
                                    <td style="padding: 25px; text-align: center;">
                                        <p style="margin: 0; color: {color_primario}; font-size: 22px; font-weight: bold;">
                                            {fecha_formateada}
                                        </p>
                                        <p style="margin: 10px 0 0 0; color: #333333; font-size: 20px;">
                                            {turno.hora_inicio.strftime('%H:%M')} - {turno.hora_fin.strftime('%H:%M')} hs
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Datos del vehículo -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid {color_primario}; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: {color_primario}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Datos del Vehículo
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 100px;">Dominio:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.vehiculo.dominio}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Marca:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.vehiculo.marca or '-'}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Modelo:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.vehiculo.modelo or '-'}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Trámite:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.tipo_vehiculo.nombre_normalizado}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Lugar de atención -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid {color_primario}; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: {color_primario}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Lugar de Atención
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 100px;">Taller:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.taller.get_nombre()}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Dirección:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_direccion() or '-'}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

{qr_section}

                    <!-- Instrucciones -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <table role="presentation" style="width: 100%; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 15px 0; color: #856404; font-size: 16px; font-weight: bold;">
                                            Instrucciones Importantes
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #856404; font-size: 14px; line-height: 1.8;">
                                            <li>Presente este comprobante impreso o en su celular al llegar.</li>
                                            <li>Llegue al menos <strong>10 minutos antes</strong> de su turno.</li>
                                            <li>Traiga el <strong>DNI</strong> del titular.</li>
                                            <li>Verifique que las luces y limpiaparabrisas funcionen correctamente.</li>
                                            <li>El tanque de combustible debe tener al menos 1/4 de carga.</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: {color_fondo}; padding: 25px 40px; text-align: center; border-top: 1px solid {color_borde};">
                            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                Este es un mensaje automático. Por favor no responda a este correo.
                            </p>
                            <p style="margin: 10px 0 0 0; color: #6c757d; font-size: 12px;">
                                Estado del turno: <strong style="color: {color_primario};">{turno.get_estado_display()}</strong>
                            </p>
                            <p style="margin: 15px 0 0 0; color: #adb5bd; font-size: 11px;">
                                RTV Pioli - Revisión Técnica Vehicular
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def enviar_email_turno(turno, motivo='confirmacion'):
    """
    Envía email de turno al cliente con imagen QR embebida correctamente.

    Args:
        turno: Instancia del modelo Turno
        motivo: 'confirmacion', 'recordatorio', 'modificacion', 'cancelacion'

    Returns:
        tuple: (success: bool, message: str)
    """
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from django.core.mail import EmailMessage

    # Verificar que el cliente tenga email
    if not turno.cliente.email:
        return False, 'El cliente no tiene email registrado'

    # Obtener conexión de email
    connection, email_config = get_email_connection()
    if not connection or not email_config:
        return False, 'No hay configuración de correo definida'

    try:
        # Obtener datos del QR
        qr_data = get_qr_image_data(turno)
        tiene_qr = qr_data is not None

        # Generar contenido HTML
        html_content = generar_html_email_turno(turno, incluir_qr=tiene_qr)

        # Generar versión texto plano
        text_content = generar_texto_email_turno(turno)

        # Definir asunto según motivo
        asuntos = {
            'confirmacion': f'Confirmación de Turno RTV - {turno.codigo}',
            'recordatorio': f'Recordatorio de Turno RTV - {turno.codigo}',
            'modificacion': f'Turno Modificado RTV - {turno.codigo}',
            'cancelacion': f'Turno Cancelado RTV - {turno.codigo}',
        }
        subject = asuntos.get(motivo, f'Turno RTV - {turno.codigo}')

        from_email = email_config.default_from_email or email_config.email_host_user

        if tiene_qr:
            # Construir email multipart manualmente para soportar imágenes inline
            # Estructura: multipart/related > multipart/alternative > text/plain + text/html
            #                               > image/png (QR)

            msg_root = MIMEMultipart('related')
            msg_root['Subject'] = subject
            msg_root['From'] = from_email
            msg_root['To'] = turno.cliente.email

            # Crear parte alternativa (texto plano + HTML)
            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)

            # Adjuntar texto plano
            msg_text = MIMEText(text_content, 'plain', 'utf-8')
            msg_alternative.attach(msg_text)

            # Adjuntar HTML
            msg_html = MIMEText(html_content, 'html', 'utf-8')
            msg_alternative.attach(msg_html)

            # Adjuntar imagen QR con Content-ID
            qr_image = MIMEImage(qr_data)
            qr_image.add_header('Content-ID', '<qr_code>')
            qr_image.add_header('Content-Disposition', 'inline', filename=f'qr_{turno.codigo}.png')
            msg_root.attach(qr_image)

            # Enviar usando la conexión SMTP
            connection.open()
            connection.connection.sendmail(
                from_email,
                [turno.cliente.email],
                msg_root.as_string()
            )
            connection.close()
        else:
            # Sin QR, usar EmailMultiAlternatives estándar
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[turno.cliente.email],
                connection=connection
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

        return True, f'Email enviado correctamente a {turno.cliente.email}'

    except Exception as e:
        return False, str(e)


def generar_texto_email_turno(turno):
    """
    Genera la versión texto plano del email (fallback).
    """
    fecha_formateada = format_fecha_legible(turno.fecha)

    texto = f"""
CONFIRMACIÓN DE TURNO - REVISIÓN TÉCNICA VEHICULAR
===================================================

Código de Turno: {turno.codigo}

Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},

Su turno ha sido registrado exitosamente.

FECHA Y HORA
------------
{fecha_formateada}
{turno.hora_inicio.strftime('%H:%M')} - {turno.hora_fin.strftime('%H:%M')} hs

DATOS DEL VEHÍCULO
------------------
Dominio: {turno.vehiculo.dominio}
Marca: {turno.vehiculo.marca or '-'}
Modelo: {turno.vehiculo.modelo or '-'}
Tipo de trámite: {turno.tipo_vehiculo.nombre_normalizado}

LUGAR DE ATENCIÓN
-----------------
Taller: {turno.taller.get_nombre()}
Dirección: {turno.taller.get_direccion() or '-'}

INSTRUCCIONES IMPORTANTES
-------------------------
* Presente este comprobante impreso o en su celular al llegar.
* Llegue al menos 10 minutos antes de su turno.
* Traiga el DNI del titular.
* Verifique que las luces y limpiaparabrisas funcionen correctamente.
* El tanque de combustible debe tener al menos 1/4 de carga.

---
Este es un mensaje automático. Por favor no responda a este correo.
Estado del turno: {turno.get_estado_display()}

RTV Pioli - Revisión Técnica Vehicular
"""
    return texto
