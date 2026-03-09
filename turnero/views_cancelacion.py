"""
Vistas para gestión de cancelación y reprogramación de turnos
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from .models import Turno, Taller, TipoVehiculo
from talleres.models import ConfiguracionTaller
from core.models import EmailConfig


def cancelar_turno_definitivo(request, turno_id):
    """
    Solicita la cancelación de un turno enviando un email con link tokenizado.
    El turno NO se cancela directamente; el cliente debe confirmar desde el email.
    """
    if request.method == 'POST':
        import json

        turno = get_object_or_404(Turno, id=turno_id)

        # Verificar que el turno puede ser cancelado
        if not turno.puede_cancelar:
            return JsonResponse({
                'success': False,
                'message': 'Este turno ya no puede ser cancelado'
            }, status=400)

        # Obtener motivo de cancelación del body (si existe)
        motivo = ''
        try:
            body = json.loads(request.body)
            motivo = body.get('motivo', '').strip()
        except (json.JSONDecodeError, ValueError):
            pass

        # Guardar motivo en observaciones (se preserva al confirmar cancelación)
        if motivo:
            obs_motivo = f"Motivo de cancelación: {motivo}"
            if turno.observaciones:
                turno.observaciones = f"{turno.observaciones}\n\n{obs_motivo}"
            else:
                turno.observaciones = obs_motivo
            turno.save(update_fields=['observaciones'])

        # Generar token de cancelación y enviar email con link seguro
        token = turno.generar_token_cancelacion()
        exito = enviar_email_solicitud_cancelacion(turno, token)

        if exito:
            return JsonResponse({
                'success': True,
                'message': f'Te enviamos un email a {turno.cliente.email} con el link para confirmar la cancelación. El link es válido por 48 horas.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Hubo un error al enviar el email. Por favor, intentá nuevamente más tarde.'
            }, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


def solicitar_reprogramacion(request, turno_id):
    """
    Inicia el proceso de reprogramación enviando un email con link seguro
    """
    if request.method == 'POST':
        turno = get_object_or_404(Turno, id=turno_id)

        # Verificar que el turno puede ser reprogramado
        if not turno.puede_reprogramar:
            return JsonResponse({
                'success': False,
                'message': 'Este turno no puede ser reprogramado. Debe faltar al menos 24 horas para el turno.'
            }, status=400)

        # Generar token de reprogramación
        token = turno.generar_token_reprogramacion()

        # Enviar email con link de reprogramación
        exito = enviar_email_reprogramacion(turno, token)

        if exito:
            return JsonResponse({
                'success': True,
                'message': 'Te enviamos un email con el link para reprogramar tu turno. El link será válido por 48 horas.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Hubo un error al enviar el email. Por favor, intentá nuevamente más tarde.'
            }, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


class ReprogramarTurnoView(View):
    """
    Vista para reprogramar un turno usando el token enviado por email
    """
    template_name = 'turnero/reprogramar_turno.html'

    def get(self, request, token):
        # Buscar turno por token
        try:
            turno = Turno.objects.get(token_reprogramacion=token)
        except Turno.DoesNotExist:
            messages.error(request, 'El link de reprogramación no es válido')
            return redirect('turnero:home')

        # Verificar que el token no haya expirado
        if not turno.token_reprogramacion_valido():
            messages.error(request, 'El link de reprogramación ha expirado. Por favor, solicitá uno nuevo.')
            return redirect('turnero:home')

        # Verificar que el turno todavía puede reprogramarse
        if not turno.puede_reprogramar:
            messages.error(request, 'Este turno ya no puede ser reprogramado')
            return redirect('turnero:home')

        # Obtener talleres disponibles para el mismo tipo de vehículo
        talleres = Taller.objects.filter(
            status=True,
            configuraciones__tipo_vehiculo=turno.tipo_vehiculo
        ).distinct()

        context = {
            'turno': turno,
            'talleres': talleres,
            'tipo_vehiculo': turno.tipo_vehiculo,
            'vehiculo': turno.vehiculo,
        }

        return render(request, self.template_name, context)

    def post(self, request, token):
        # Buscar turno por token
        try:
            turno = Turno.objects.get(token_reprogramacion=token)
        except Turno.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Token inválido'}, status=400)

        # Verificar validez del token
        if not turno.token_reprogramacion_valido():
            return JsonResponse({'success': False, 'message': 'Token expirado'}, status=400)

        # Obtener datos del formulario
        taller_id = request.POST.get('taller')
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')

        if not all([taller_id, fecha, hora_inicio]):
            return JsonResponse({'success': False, 'message': 'Faltan datos'}, status=400)

        # Actualizar turno
        try:
            from datetime import datetime
            taller = Taller.objects.get(id=taller_id)

            turno.taller = taller
            turno.fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            turno.hora_inicio = datetime.strptime(hora_inicio, '%H:%M').time()

            # Calcular hora_fin usando el intervalo de la configuración del taller
            from datetime import timedelta
            try:
                config = ConfiguracionTaller.objects.get(
                    taller=taller,
                    tipo_vehiculo=turno.tipo_vehiculo
                )
                duracion_minutos = config.intervalo_minutos
            except ConfiguracionTaller.DoesNotExist:
                # Fallback al duracion_minutos del tipo de vehículo
                duracion_minutos = turno.tipo_vehiculo.duracion_minutos

            duracion = timedelta(minutes=duracion_minutos)
            hora_inicio_dt = datetime.combine(turno.fecha, turno.hora_inicio)
            hora_fin_dt = hora_inicio_dt + duracion
            turno.hora_fin = hora_fin_dt.time()

            # Invalidar el token (ya fue usado)
            turno.token_reprogramacion = None
            turno.token_expiracion = None

            turno.save()

            # Enviar email de confirmación de reprogramación
            enviar_email_confirmacion_reprogramacion(turno)

            return JsonResponse({
                'success': True,
                'message': 'Tu turno ha sido reprogramado exitosamente',
                'redirect_url': reverse('turnero:consultar_turno')
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al reprogramar: {str(e)}'
            }, status=500)


class CancelarTurnoView(View):
    """
    Vista para cancelar un turno usando el token enviado por email.
    GET: muestra página de confirmación con datos del turno.
    POST: ejecuta la cancelación.
    """
    template_name = 'turnero/cancelar_turno.html'

    def get(self, request, token):
        try:
            turno = Turno.objects.select_related(
                'taller', 'vehiculo', 'cliente', 'tipo_vehiculo'
            ).get(token_cancelacion=token)
        except Turno.DoesNotExist:
            messages.error(request, 'El link de cancelación no es válido.')
            return redirect('turnero:home')

        if not turno.token_cancelacion_valido():
            messages.error(request, 'El link de cancelación ha expirado. Por favor, solicitá uno nuevo.')
            return redirect('turnero:home')

        if not turno.puede_cancelar:
            messages.error(request, 'Este turno ya no puede ser cancelado.')
            return redirect('turnero:home')

        return render(request, self.template_name, {'turno': turno})

    def post(self, request, token):
        try:
            turno = Turno.objects.select_related(
                'taller', 'vehiculo', 'cliente', 'tipo_vehiculo'
            ).get(token_cancelacion=token)
        except Turno.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Token inválido'}, status=400)

        if not turno.token_cancelacion_valido():
            return JsonResponse({'success': False, 'message': 'Token expirado'}, status=400)

        if not turno.puede_cancelar:
            return JsonResponse({'success': False, 'message': 'Este turno ya no puede ser cancelado'}, status=400)

        # Ejecutar cancelación
        turno.estado = 'CANCELADO'
        obs = 'Cancelación confirmada por el cliente desde enlace de email'
        if turno.observaciones:
            turno.observaciones = f"{turno.observaciones}\n\n{obs}"
        else:
            turno.observaciones = obs

        # Invalidar token
        turno.token_cancelacion = None
        turno.token_cancelacion_expiracion = None
        turno.save()

        # Extraer motivo de las observaciones (si existe)
        motivo = ''
        if turno.observaciones and 'Motivo de cancelación:' in turno.observaciones:
            for linea in turno.observaciones.split('\n'):
                if linea.strip().startswith('Motivo de cancelación:'):
                    motivo = linea.strip().replace('Motivo de cancelación:', '').strip()
                    break

        # Enviar email de confirmación (con motivo si existe)
        enviar_email_cancelacion(turno, motivo)

        return JsonResponse({
            'success': True,
            'message': 'Tu turno ha sido cancelado exitosamente',
            'redirect_url': reverse('turnero:consultar_turno')
        })


def enviar_email_solicitud_cancelacion(turno, token):
    """
    Envía email HTML con link para confirmar la cancelación del turno.
    Similar al flujo de reprogramación: el usuario debe abrir el link para cancelar.
    """
    try:
        from django.conf import settings
        email_config = EmailConfig.objects.first()

        if not email_config:
            return False

        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=email_config.email_host,
            port=email_config.email_port,
            username=email_config.email_host_user,
            password=email_config.email_host_password,
            use_tls=email_config.email_use_tls,
        )

        site_url = settings.SITE_URL

        cancelar_url = f"{site_url}/turnero/cancelar/{token}/"

        subject = f"Cancelar Turno RTV - {turno.codigo}"

        body_text = (
            f"Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},\n\n"
            f"Ha solicitado cancelar su turno de Revisión Técnica Vehicular.\n\n"
            f"Código de Turno: {turno.codigo}\n"
            f"Vehículo: {turno.vehiculo.dominio}\n"
            f"Fecha: {turno.fecha.strftime('%d/%m/%Y')}\n"
            f"Horario: {turno.hora_inicio.strftime('%H:%M')} hs\n"
            f"Taller: {turno.taller.get_nombre()}\n\n"
            f"Para confirmar la cancelación, ingrese al siguiente enlace:\n"
            f"{cancelar_url}\n\n"
            f"Este enlace es válido por 48 horas.\n"
            f"Si usted no solicitó esta cancelación, puede ignorar este mensaje.\n\n"
            f"Saludos cordiales,\nRTV Pioli - Revisión Técnica Vehicular"
        )

        color_primario = "#13304D"
        color_secundario = "#1a4a73"
        color_fondo = "#f8f9fa"
        color_borde = "#e9ecef"
        color_danger = "#ef4444"

        body_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cancelar Turno - {turno.codigo}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {color_fondo};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {color_danger} 0%, #f87171 100%); padding: 30px 40px; text-align: center;">
                            <img src="cid:logo_rtv" alt="RTV Pioli" style="width: 80px; height: auto; margin-bottom: 15px; border-radius: 12px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                Cancelar Turno
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
                                Código de turno
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
                                Ha solicitado cancelar su turno de Revisión Técnica Vehicular. A continuación encontrará los datos del turno:
                            </p>
                        </td>
                    </tr>

                    <!-- Datos del turno -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid {color_danger}; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: {color_danger}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Turno a Cancelar
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 120px;">Vehículo:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.vehiculo.dominio}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Fecha:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.fecha.strftime('%d/%m/%Y')}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Horario:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.hora_inicio.strftime('%H:%M')} hs</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Taller:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_nombre()}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Dirección:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_direccion()}, {turno.taller.get_localidad().nombre}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Botón de cancelación -->
                    <tr>
                        <td style="padding: 10px 40px 30px 40px; text-align: center;">
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px;">
                                Haga clic en el siguiente botón para confirmar la cancelación:
                            </p>
                            <table role="presentation" style="margin: 0 auto;">
                                <tr>
                                    <td style="background: linear-gradient(135deg, {color_danger} 0%, #f87171 100%); border-radius: 10px;">
                                        <a href="{cancelar_url}" target="_blank" style="display: inline-block; padding: 16px 40px; color: #ffffff; text-decoration: none; font-size: 18px; font-weight: bold; letter-spacing: 0.5px;">
                                            Cancelar mi Turno
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 15px 0 0 0; color: #6c757d; font-size: 12px;">
                                Si el botón no funciona, copie y pegue este enlace en su navegador:<br>
                                <a href="{cancelar_url}" style="color: {color_secundario}; word-break: break-all;">{cancelar_url}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Advertencia -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <table role="presentation" style="width: 100%; background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 15px 0; color: #991b1b; font-size: 16px; font-weight: bold;">
                                            Importante
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #991b1b; font-size: 14px; line-height: 1.8;">
                                            <li>Este enlace es válido por <strong>48 horas</strong>.</li>
                                            <li>La cancelación <strong>no se puede deshacer</strong>.</li>
                                            <li>Si cambia de opinión, puede sacar un nuevo turno desde nuestra web.</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Nota de seguridad -->
                    <tr>
                        <td style="padding: 0 40px 25px 40px;">
                            <p style="margin: 0; color: #6c757d; font-size: 13px; font-style: italic;">
                                Si usted no solicitó esta cancelación, puede ignorar este mensaje. Su turno se mantiene sin cambios.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: {color_fondo}; padding: 25px 40px; text-align: center; border-top: 1px solid {color_borde};">
                            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                Este es un mensaje automático. Por favor no responda a este correo.
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

        from .utils import enviar_email_html_con_logo
        enviar_email_html_con_logo(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            to_email=turno.cliente.email,
            connection=connection,
            from_email=email_config.default_from_email or email_config.email_host_user,
        )
        return True

    except Exception as e:
        print(f"Error al enviar email de solicitud de cancelación: {e}")
        return False


def enviar_email_cancelacion(turno, motivo=''):
    """
    Envía email HTML de confirmación de cancelación (post-cancelación).
    """
    try:
        from django.conf import settings
        email_config = EmailConfig.objects.first()

        if not email_config:
            return False

        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=email_config.email_host,
            port=email_config.email_port,
            username=email_config.email_host_user,
            password=email_config.email_host_password,
            use_tls=email_config.email_use_tls,
        )

        site_url = settings.SITE_URL

        nuevo_turno_url = f"{site_url}/turnero/paso1/"

        # Sección de motivo para texto plano
        motivo_text = ""
        if motivo:
            motivo_text = f"\nMotivo de cancelación: {motivo}\n"

        subject = f"Turno RTV Cancelado - {turno.codigo}"

        body_text = (
            f"Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},\n\n"
            f"Su turno ha sido cancelado exitosamente.\n\n"
            f"Código de Turno: {turno.codigo}\n"
            f"Vehículo: {turno.vehiculo.dominio}\n"
            f"Fecha: {turno.fecha.strftime('%d/%m/%Y')}\n"
            f"Horario: {turno.hora_inicio.strftime('%H:%M')} hs\n"
            f"Taller: {turno.taller.get_nombre()}\n"
            f"{motivo_text}\n"
            f"Si desea agendar un nuevo turno: {nuevo_turno_url}\n\n"
            f"Saludos cordiales,\nRTV Pioli - Revisión Técnica Vehicular"
        )

        color_primario = "#13304D"
        color_fondo = "#f8f9fa"
        color_borde = "#e9ecef"
        color_danger = "#ef4444"
        color_success = "#10b981"

        # Sección de motivo para HTML
        motivo_html = ""
        if motivo:
            motivo_html = f"""
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid #6c757d; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: #6c757d; font-size: 14px; font-weight: bold;">
                                            Motivo de cancelación
                                        </p>
                                        <p style="margin: 5px 0 0 0; color: #333333; font-size: 14px;">
                                            {motivo}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
"""

        body_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Turno Cancelado - {turno.codigo}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {color_fondo};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%); padding: 30px 40px; text-align: center;">
                            <img src="cid:logo_rtv" alt="RTV Pioli" style="width: 80px; height: auto; margin-bottom: 15px; border-radius: 12px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                Turno Cancelado
                            </h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                Revisión Técnica Vehicular
                            </p>
                        </td>
                    </tr>

                    <!-- Código de turno tachado -->
                    <tr>
                        <td style="padding: 30px 40px 20px 40px; text-align: center;">
                            <div style="display: inline-block; background-color: #6b7280; color: #ffffff; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 2px; text-decoration: line-through;">
                                {turno.codigo}
                            </div>
                            <p style="margin: 15px 0 0 0; color: {color_danger}; font-size: 14px; font-weight: bold;">
                                CANCELADO
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
                                Le confirmamos que su turno ha sido cancelado exitosamente.
                            </p>
                        </td>
                    </tr>

                    <!-- Datos del turno cancelado -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid #6b7280; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Datos del Turno Cancelado
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 120px;">Vehículo:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.vehiculo.dominio}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Fecha:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; text-decoration: line-through;">{turno.fecha.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')} hs</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Taller:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_nombre()}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    {motivo_html}

                    <!-- Botón nuevo turno -->
                    <tr>
                        <td style="padding: 10px 40px 30px 40px; text-align: center;">
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px;">
                                Si necesitás, podés sacar un nuevo turno:
                            </p>
                            <table role="presentation" style="margin: 0 auto;">
                                <tr>
                                    <td style="background: linear-gradient(135deg, {color_success} 0%, #34d399 100%); border-radius: 10px;">
                                        <a href="{nuevo_turno_url}" target="_blank" style="display: inline-block; padding: 16px 40px; color: #ffffff; text-decoration: none; font-size: 18px; font-weight: bold; letter-spacing: 0.5px;">
                                            Sacar Nuevo Turno
                                        </a>
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

        from .utils import enviar_email_html_con_logo
        enviar_email_html_con_logo(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            to_email=turno.cliente.email,
            connection=connection,
            from_email=email_config.default_from_email or email_config.email_host_user,
        )
        return True

    except Exception as e:
        print(f"Error al enviar email de cancelación: {e}")
        return False


def enviar_email_reprogramacion(turno, token):
    """
    Envía email con link para reprogramar el turno (HTML profesional)
    """
    try:
        from django.conf import settings
        email_config = EmailConfig.objects.first()

        if not email_config:
            return False

        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=email_config.email_host,
            port=email_config.email_port,
            username=email_config.email_host_user,
            password=email_config.email_host_password,
            use_tls=email_config.email_use_tls,
        )

        site_url = settings.SITE_URL

        reprogramar_url = f"{site_url}/turnero/reprogramar/{token}/"

        subject = f"Reprogramar Turno RTV - {turno.codigo}"

        # Texto plano (fallback)
        body_text = (
            f"Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},\n\n"
            f"Ha solicitado reprogramar su turno de Revisión Técnica Vehicular.\n\n"
            f"Código de Turno: {turno.codigo}\n"
            f"Vehículo: {turno.vehiculo.dominio}\n"
            f"Fecha Actual: {turno.fecha.strftime('%d/%m/%Y')}\n"
            f"Horario Actual: {turno.hora_inicio.strftime('%H:%M')} hs\n"
            f"Taller: {turno.taller.get_nombre()}\n\n"
            f"Para reprogramar su turno, ingrese al siguiente enlace:\n"
            f"{reprogramar_url}\n\n"
            f"Este enlace es válido por 48 horas y solo puede usarse una vez.\n\n"
            f"Saludos cordiales,\nRTV Pioli - Revisión Técnica Vehicular"
        )

        # HTML profesional
        color_primario = "#13304D"
        color_secundario = "#1a4a73"
        color_fondo = "#f8f9fa"
        color_borde = "#e9ecef"
        color_acento = "#f59e0b"

        body_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reprogramar Turno - {turno.codigo}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {color_fondo};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {color_acento} 0%, #fbbf24 100%); padding: 30px 40px; text-align: center;">
                            <img src="cid:logo_rtv" alt="RTV Pioli" style="width: 80px; height: auto; margin-bottom: 15px; border-radius: 12px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                Reprogramar Turno
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
                                Código de turno
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
                                Ha solicitado reprogramar su turno de Revisión Técnica Vehicular. A continuación encontrará los datos de su turno actual:
                            </p>
                        </td>
                    </tr>

                    <!-- Datos del turno actual -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid {color_primario}; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: {color_primario}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Turno Actual
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 120px;">Vehículo:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.vehiculo.dominio}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Fecha actual:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.fecha.strftime('%d/%m/%Y')}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Horario actual:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.hora_inicio.strftime('%H:%M')} hs</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Taller:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_nombre()}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Dirección:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_direccion()}, {turno.taller.get_localidad().nombre}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Botón de reprogramación -->
                    <tr>
                        <td style="padding: 10px 40px 30px 40px; text-align: center;">
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px;">
                                Haga clic en el siguiente botón para elegir la nueva fecha y horario:
                            </p>
                            <table role="presentation" style="margin: 0 auto;">
                                <tr>
                                    <td style="background: linear-gradient(135deg, {color_acento} 0%, #fbbf24 100%); border-radius: 10px;">
                                        <a href="{reprogramar_url}" target="_blank" style="display: inline-block; padding: 16px 40px; color: #ffffff; text-decoration: none; font-size: 18px; font-weight: bold; letter-spacing: 0.5px;">
                                            Reprogramar mi Turno
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 15px 0 0 0; color: #6c757d; font-size: 12px;">
                                Si el botón no funciona, copie y pegue este enlace en su navegador:<br>
                                <a href="{reprogramar_url}" style="color: {color_secundario}; word-break: break-all;">{reprogramar_url}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Instrucciones importantes -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <table role="presentation" style="width: 100%; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 15px 0; color: #856404; font-size: 16px; font-weight: bold;">
                                            Importante
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #856404; font-size: 14px; line-height: 1.8;">
                                            <li>Este enlace es válido por <strong>48 horas</strong>.</li>
                                            <li>Solo puede usarse <strong>una vez</strong>.</li>
                                            <li>Debe faltar al menos <strong>24 horas</strong> para el turno original.</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Nota de seguridad -->
                    <tr>
                        <td style="padding: 0 40px 25px 40px;">
                            <p style="margin: 0; color: #6c757d; font-size: 13px; font-style: italic;">
                                Si usted no solicitó esta reprogramación, puede ignorar este mensaje. Su turno original se mantiene sin cambios.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: {color_fondo}; padding: 25px 40px; text-align: center; border-top: 1px solid {color_borde};">
                            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                Este es un mensaje automático. Por favor no responda a este correo.
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

        from .utils import enviar_email_html_con_logo
        enviar_email_html_con_logo(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            to_email=turno.cliente.email,
            connection=connection,
            from_email=email_config.default_from_email or email_config.email_host_user,
        )
        return True

    except Exception as e:
        print(f"Error al enviar email de reprogramación: {e}")
        return False


def enviar_email_confirmacion_reprogramacion(turno):
    """
    Envía email HTML profesional de confirmación después de reprogramar exitosamente.
    """
    try:
        from django.conf import settings
        email_config = EmailConfig.objects.first()

        if not email_config:
            return False

        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=email_config.email_host,
            port=email_config.email_port,
            username=email_config.email_host_user,
            password=email_config.email_host_password,
            use_tls=email_config.email_use_tls,
        )

        site_url = settings.SITE_URL

        consultar_url = f"{site_url}/turnero/consultar/"

        subject = f"Turno Reprogramado - {turno.codigo}"

        body_text = (
            f"Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},\n\n"
            f"Su turno ha sido reprogramado exitosamente.\n\n"
            f"Código de Turno: {turno.codigo}\n"
            f"Vehículo: {turno.vehiculo.dominio}\n"
            f"Trámite: {turno.tipo_vehiculo.nombre}\n"
            f"Nueva Fecha: {turno.fecha.strftime('%d/%m/%Y')}\n"
            f"Nuevo Horario: {turno.hora_inicio.strftime('%H:%M')} hs\n"
            f"Taller: {turno.taller.get_nombre()}\n"
            f"Dirección: {turno.taller.get_direccion()}, {turno.taller.get_localidad().nombre}\n"
            f"Teléfono: {turno.taller.get_telefono()}\n\n"
            f"Recordatorios:\n"
            f"- Presentese 10 minutos antes del horario asignado\n"
            f"- Traiga DNI, cédula del vehículo y comprobante de pago\n"
            f"- El vehículo debe estar en condiciones técnicas adecuadas\n\n"
            f"Si necesita cancelar este turno, puede hacerlo hasta 24 horas antes.\n\n"
            f"Consultar su turno: {consultar_url}\n\n"
            f"Saludos cordiales,\nRTV Pioli - Revisión Técnica Vehicular"
        )

        color_primario = "#13304D"
        color_fondo = "#f8f9fa"
        color_borde = "#e9ecef"
        color_success = "#10b981"

        body_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Turno Reprogramado - {turno.codigo}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {color_fondo};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {color_success} 0%, #34d399 100%); padding: 30px 40px; text-align: center;">
                            <img src="cid:logo_rtv" alt="RTV Pioli" style="width: 80px; height: auto; margin-bottom: 15px; border-radius: 12px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 600;">
                                Turno Reprogramado
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
                            <p style="margin: 15px 0 0 0; color: {color_success}; font-size: 14px; font-weight: bold;">
                                REPROGRAMADO EXITOSAMENTE
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
                                Su turno ha sido reprogramado exitosamente. A continuación encontrará los nuevos datos:
                            </p>
                        </td>
                    </tr>

                    <!-- Nuevos datos del turno -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid {color_success}; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: {color_success}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Nuevos Datos del Turno
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 120px;">Vehículo:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.vehiculo.dominio}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Trámite:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.tipo_vehiculo.nombre}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Nueva Fecha:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.fecha.strftime('%d/%m/%Y')}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Nuevo Horario:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.hora_inicio.strftime('%H:%M')} hs</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Datos del taller -->
                    <tr>
                        <td style="padding: 0 40px 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 15px; background-color: {color_fondo}; border-left: 4px solid {color_primario}; border-radius: 0 8px 8px 0;">
                                        <p style="margin: 0 0 5px 0; color: {color_primario}; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                                            Taller Asignado
                                        </p>
                                        <table role="presentation" style="width: 100%; margin-top: 10px;">
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px; width: 120px;">Taller:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px; font-weight: bold;">{turno.taller.get_nombre()}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Dirección:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_direccion()}, {turno.taller.get_localidad().nombre}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 5px 0; color: #6c757d; font-size: 14px;">Teléfono:</td>
                                                <td style="padding: 5px 0; color: #333333; font-size: 14px;">{turno.taller.get_telefono()}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Recordatorios -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px;">
                            <table role="presentation" style="width: 100%; background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="margin: 0 0 15px 0; color: #1e40af; font-size: 16px; font-weight: bold;">
                                            Recordatorios Importantes
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #1e40af; font-size: 14px; line-height: 1.8;">
                                            <li>Presentese <strong>10 minutos antes</strong> del horario asignado.</li>
                                            <li>Traiga <strong>DNI, cédula del vehículo</strong> y comprobante de pago.</li>
                                            <li>El vehículo debe estar en <strong>condiciones técnicas adecuadas</strong>.</li>
                                            <li>Si necesita cancelar, puede hacerlo hasta <strong>24 horas antes</strong>.</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Botón consultar turno -->
                    <tr>
                        <td style="padding: 0 40px 30px 40px; text-align: center;">
                            <table role="presentation" style="margin: 0 auto;">
                                <tr>
                                    <td style="background: linear-gradient(135deg, {color_primario} 0%, #1a4a73 100%); border-radius: 10px;">
                                        <a href="{consultar_url}" target="_blank" style="display: inline-block; padding: 16px 40px; color: #ffffff; text-decoration: none; font-size: 18px; font-weight: bold; letter-spacing: 0.5px;">
                                            Consultar mi Turno
                                        </a>
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

        from .utils import enviar_email_html_con_logo
        enviar_email_html_con_logo(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            to_email=turno.cliente.email,
            connection=connection,
            from_email=email_config.default_from_email or email_config.email_host_user,
        )
        return True

    except Exception as e:
        print(f"Error al enviar email de confirmación de reprogramación: {e}")
        return False
