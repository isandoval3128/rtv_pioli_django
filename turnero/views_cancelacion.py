"""
Vistas para gestión de cancelación y reprogramación de turnos
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.core.mail import EmailMessage, get_connection
from .models import Turno, Taller, TipoVehiculo
from talleres.models import ConfiguracionTaller
from core.models import EmailConfig


def cancelar_turno_definitivo(request, turno_id):
    """
    Cancela un turno de forma definitiva (sin posibilidad de reprogramar)
    """
    if request.method == 'POST':
        turno = get_object_or_404(Turno, id=turno_id)

        # Verificar que el turno puede ser cancelado
        if not turno.puede_cancelar:
            return JsonResponse({
                'success': False,
                'message': 'Este turno ya no puede ser cancelado'
            }, status=400)

        # Cambiar estado a CANCELADO
        turno.estado = 'CANCELADO'
        turno.save()

        # Enviar email de confirmación de cancelación
        enviar_email_cancelacion(turno)

        return JsonResponse({
            'success': True,
            'message': 'Tu turno ha sido cancelado exitosamente'
        })

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


def enviar_email_cancelacion(turno):
    """
    Envía email de confirmación de cancelación de turno
    """
    try:
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

        subject = f"Turno RTV Cancelado - {turno.codigo}"
        body = f"""
Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},

Su turno ha sido cancelado exitosamente:

Código de Turno: {turno.codigo}
Vehículo: {turno.vehiculo.dominio}
Fecha Original: {turno.fecha.strftime('%d/%m/%Y')}
Horario Original: {turno.hora_inicio.strftime('%H:%M')} hs
Taller: {turno.taller.get_nombre()}

Si desea agendar un nuevo turno, puede hacerlo a través de nuestra página web.

Saludos cordiales,
RTV Pioli
"""

        email = EmailMessage(
            subject,
            body,
            email_config.default_from_email or email_config.email_host_user,
            [turno.cliente.email],
            connection=connection
        )

        email.send(fail_silently=False)
        return True

    except Exception as e:
        print(f"Error al enviar email de cancelación: {e}")
        return False


def enviar_email_reprogramacion(turno, token):
    """
    Envía email con link para reprogramar el turno
    """
    try:
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

        # Generar URL completa para reprogramar
        # Usar localhost:8000 por defecto en desarrollo
        domain = 'localhost:8000'

        reprogramar_url = f"http://{domain}/turnero/reprogramar/{token}/"

        subject = f"Reprogramar Turno RTV - {turno.codigo}"
        body = f"""
Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},

Ha solicitado reprogramar su turno de Revisión Técnica Vehicular.

Datos del turno actual:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Código de Turno: {turno.codigo}
Vehículo: {turno.vehiculo.dominio}
Fecha Actual: {turno.fecha.strftime('%d/%m/%Y')}
Horario Actual: {turno.hora_inicio.strftime('%H:%M')} hs
Taller: {turno.taller.get_nombre()}
Dirección: {turno.taller.get_direccion()}, {turno.taller.get_localidad().nombre}

Para reprogramar su turno, ingrese al siguiente enlace:

{reprogramar_url}

IMPORTANTE:
• Este enlace es válido por 48 horas
• Solo puede usarse una vez
• Debe faltar al menos 24 horas para el turno original

Si no solicitó esta reprogramación, ignore este mensaje.

Saludos cordiales,
RTV Pioli - Revisión Técnica Vehicular
"""

        email = EmailMessage(
            subject,
            body,
            email_config.default_from_email or email_config.email_host_user,
            [turno.cliente.email],
            connection=connection
        )

        email.send(fail_silently=False)
        return True

    except Exception as e:
        print(f"Error al enviar email de reprogramación: {e}")
        return False


def enviar_email_confirmacion_reprogramacion(turno):
    """
    Envía email de confirmación después de reprogramar exitosamente
    """
    try:
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

        subject = f"Turno Reprogramado - {turno.codigo}"
        body = f"""
Estimado/a {turno.cliente.nombre} {turno.cliente.apellido},

Su turno ha sido reprogramado exitosamente.

Nuevos datos del turno:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Código de Turno: {turno.codigo}
Vehículo: {turno.vehiculo.dominio}
Trámite: {turno.tipo_vehiculo.nombre}

📅 Nueva Fecha: {turno.fecha.strftime('%d/%m/%Y')}
🕐 Nuevo Horario: {turno.hora_inicio.strftime('%H:%M')} hs

📍 Taller: {turno.taller.get_nombre()}
📍 Dirección: {turno.taller.get_direccion()}, {turno.taller.get_localidad().nombre}
📞 Teléfono: {turno.taller.get_telefono()}

RECORDATORIOS IMPORTANTES:
✓ Presentese 10 minutos antes del horario asignado
✓ Traiga DNI, cédula del vehículo y comprobante de pago
✓ El vehículo debe estar en condiciones técnicas adecuadas

Si necesita cancelar este turno, puede hacerlo hasta 24 horas antes.

Saludos cordiales,
RTV Pioli - Revisión Técnica Vehicular
"""

        email = EmailMessage(
            subject,
            body,
            email_config.default_from_email or email_config.email_host_user,
            [turno.cliente.email],
            connection=connection
        )

        email.send(fail_silently=False)
        return True

    except Exception as e:
        print(f"Error al enviar email de confirmación: {e}")
        return False
