"""
Módulo de escalación/derivación a operador humano.
Maneja: verificación de horario, link WhatsApp, email, flujo conversacional.
"""
import re
import urllib.parse

from django.utils import timezone

from .resolver import ResolverResult


def esta_en_horario(taller):
    """Verifica si el taller está dentro de su horario de atención ahora"""
    ahora = timezone.localtime()
    hora_actual = ahora.time()

    # Verificar hora
    if not (taller.horario_apertura <= hora_actual <= taller.horario_cierre):
        return False

    # Verificar día de la semana
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_actual = dias_semana[ahora.weekday()]
    dias = taller.dias_atencion or {}

    if not dias.get(dia_actual, False):
        return False

    # Verificar fechas no laborables
    fecha_str = ahora.strftime('%Y-%m-%d')
    fechas_no_lab = taller.fechas_no_laborables or []
    if fecha_str in fechas_no_lab:
        return False

    return True


def generar_resumen_conversacion(session, max_mensajes=8, max_chars=300):
    """Genera un resumen corto de la conversación para WA o email"""
    from asistente.models import ChatMessage

    mensajes = ChatMessage.objects.filter(
        session=session
    ).order_by('-created_at')[:max_mensajes]

    mensajes = list(reversed(mensajes))
    partes = []
    for msg in mensajes:
        rol = 'Cliente' if msg.rol == 'user' else 'Asistente'
        partes.append(f"{rol}: {msg.contenido[:100]}")

    resumen = ' | '.join(partes)
    if len(resumen) > max_chars:
        resumen = resumen[:max_chars] + '...'
    return resumen


def generar_resumen_email(session, max_mensajes=15):
    """Genera resumen completo para email (sin límite de chars)"""
    from asistente.models import ChatMessage

    mensajes = ChatMessage.objects.filter(
        session=session
    ).order_by('created_at')[:max_mensajes]

    lineas = []
    for msg in mensajes:
        rol = 'Cliente' if msg.rol == 'user' else 'Asistente'
        hora = msg.created_at.strftime('%H:%M')
        lineas.append(f"[{hora}] {rol}: {msg.contenido}")

    return '\n'.join(lineas)


def generar_link_whatsapp(numero, resumen):
    """Genera link wa.me con texto pre-cargado"""
    texto = f"Hola, vengo del asistente virtual. {resumen}"
    return f"https://wa.me/{numero}?text={urllib.parse.quote(texto)}"


def enviar_email_derivacion(taller, session, resumen, celular_cliente=''):
    """Envía email formal al taller informando la derivación"""
    from django.core.mail import EmailMultiAlternatives
    from turnero.utils import get_email_connection
    from asistente.models import Derivacion

    connection, email_config = get_email_connection()
    if not connection or not email_config:
        return False

    email_destino = taller.get_email_operador()
    if not email_destino:
        return False

    nombre_taller = taller.get_nombre()
    from_email = email_config.default_from_email or email_config.email_host_user

    # Datos del cliente
    ip_cliente = session.ip_address or 'No disponible'
    fecha_sesion = session.inicio.strftime('%d/%m/%Y %H:%M')

    asunto = f'Solicitud de atención - Asistente Virtual RTV'

    # Texto plano
    texto = (
        f"Estimado equipo de {nombre_taller},\n\n"
        f"Un cliente solicitó atención personalizada a través del asistente virtual "
        f"fuera del horario de atención.\n\n"
        f"--- DATOS DEL CLIENTE ---\n"
        f"IP: {ip_cliente}\n"
        f"Sesión iniciada: {fecha_sesion}\n"
    )
    if celular_cliente:
        texto += f"Celular (para contacto por WhatsApp): {celular_cliente}\n"
    texto += (
        f"\n--- RESUMEN DE LA CONVERSACIÓN ---\n"
        f"{resumen}\n\n"
        f"Se sugiere contactar al cliente a la brevedad.\n\n"
        f"---\n"
        f"Este mensaje fue generado automáticamente por el Asistente Virtual.\n"
    )

    # HTML
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #003466 0%, #0056b3 100%); padding: 20px 30px; border-radius: 8px 8px 0 0;">
            <h2 style="color: #fff; margin: 0; font-size: 18px;">Solicitud de Atención - Asistente Virtual</h2>
        </div>
        <div style="background: #fff; padding: 25px 30px; border: 1px solid #e0e0e0;">
            <p>Estimado equipo de <strong>{nombre_taller}</strong>,</p>
            <p>Un cliente solicitó atención personalizada a través del asistente virtual
            fuera del horario de atención.</p>

            <div style="background: #f8f9fa; border-left: 4px solid #003466; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                <h3 style="margin: 0 0 10px; color: #003466; font-size: 14px;">Datos del Cliente</h3>
                <p style="margin: 5px 0; font-size: 13px;"><strong>IP:</strong> {ip_cliente}</p>
                <p style="margin: 5px 0; font-size: 13px;"><strong>Sesión:</strong> {fecha_sesion}</p>
                {'<p style="margin: 5px 0; font-size: 13px;"><strong>Celular:</strong> ' + celular_cliente + '</p>' if celular_cliente else ''}
            </div>

            {'<div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;"><p style="margin: 0; font-size: 13px;"><strong>El cliente dejó su celular para ser contactado por WhatsApp:</strong> ' + celular_cliente + '</p></div>' if celular_cliente else ''}

            <div style="background: #f8f9fa; border-left: 4px solid #6c757d; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                <h3 style="margin: 0 0 10px; color: #333; font-size: 14px;">Resumen de la Conversación</h3>
                <pre style="white-space: pre-wrap; font-size: 12px; line-height: 1.6; margin: 0; font-family: 'Segoe UI', Arial, sans-serif;">{resumen}</pre>
            </div>

            <p style="color: #666; font-size: 13px;">Se sugiere contactar al cliente a la brevedad.</p>
        </div>
        <div style="background: #f8f9fa; padding: 12px 30px; border-radius: 0 0 8px 8px; border: 1px solid #e0e0e0; border-top: none;">
            <p style="margin: 0; font-size: 11px; color: #999; text-align: center;">
                Mensaje generado automáticamente por el Asistente Virtual RTV
            </p>
        </div>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=from_email,
            to=[email_destino],
            connection=connection,
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error enviando email derivación: {e}")
        return False


def procesar_derivacion_inicial(taller, intent, confidence):
    """Procesa la derivación una vez que se seleccionó el taller"""
    nombre = taller.get_nombre()

    if esta_en_horario(taller):
        whatsapp = taller.get_whatsapp_operador()
        if not whatsapp:
            return ResolverResult(
                intent=intent,
                respuesta_fija=(
                    f'Ahora mismo {nombre} está en horario de atención, '
                    f'pero no tenemos un número de WhatsApp configurado. '
                    f'Podés comunicarte por teléfono al {taller.get_telefono() or "número del taller"}.'
                ),
                source='hardcoded', confidence=confidence,
            )

        return ResolverResult(
            intent=intent,
            respuesta_fija=None,
            datos=f'derivacion_whatsapp|{taller.pk}',
            source='db',
            necesita_humanizar=False,
            confidence=confidence,
        )
    else:
        return ResolverResult(
            intent=intent,
            respuesta_fija=None,
            datos=f'derivacion_email|{taller.pk}',
            source='db',
            necesita_humanizar=False,
            confidence=confidence,
        )


def procesar_contexto_pendiente(session, mensaje):
    """
    Procesa flujos conversacionales pendientes en session.contexto.
    Retorna (respuesta, intent, acciones) o None si no hay contexto pendiente.
    """
    from asistente.models import Derivacion
    from talleres.models import Taller

    contexto = session.contexto or {}
    esperando = contexto.get('esperando')

    if not esperando:
        return None

    if esperando == 'seleccion_planta':
        # El usuario eligió una planta (puede ser texto del botón o accion_id)
        taller = _identificar_taller(mensaje, contexto)
        if not taller:
            return {
                'respuesta': 'No pude identificar la planta. ¿Podés indicarme cuál elegís?',
                'intent': 'hablar_con_operador',
                'acciones': contexto.get('acciones_previas', []),
                'source': 'hardcoded',
            }

        # Limpiar contexto de selección
        session.contexto = {}
        session.save(update_fields=['contexto'])

        # Procesar según horario
        if esta_en_horario(taller):
            return _procesar_whatsapp(session, taller)
        else:
            # Guardar taller y pedir celular
            session.contexto = {
                'esperando': 'celular_cliente',
                'taller_id': taller.pk,
            }
            session.save(update_fields=['contexto'])
            nombre = taller.get_nombre()
            return {
                'respuesta': (
                    f'🕐 En este momento {nombre} está fuera del horario de atención. '
                    f'Si querés, dejame tu número de celular así te contactan por WhatsApp, '
                    f'o escribí "enviar" y le mando tu consulta por email al equipo.'
                ),
                'intent': 'hablar_con_operador',
                'acciones': [
                    {'texto': '📧 Enviar sin celular', 'accion': 'enviar_email_sin_cel'},
                ],
                'source': 'hardcoded',
            }

    elif esperando == 'celular_cliente':
        taller_id = contexto.get('taller_id')
        try:
            taller = Taller.objects.get(pk=taller_id, status=True)
        except Taller.DoesNotExist:
            session.contexto = {}
            session.save(update_fields=['contexto'])
            return {
                'respuesta': 'Hubo un problema. ¿Podés volver a intentar?',
                'intent': 'hablar_con_operador',
                'acciones': [],
                'source': 'hardcoded',
            }

        # Detectar si dio un celular o quiere enviar sin
        celular = _extraer_celular(mensaje)
        quiere_enviar = mensaje.lower().strip() in [
            'enviar', 'enviar email', 'enviar sin celular', 'no', 'no tengo',
        ] or mensaje.startswith('enviar_email_sin_cel')

        if not celular and not quiere_enviar:
            # Podría ser un celular mal escrito o un texto random
            # Intentar interpretar como celular limpiando caracteres
            numeros = re.sub(r'[^\d]', '', mensaje)
            if len(numeros) >= 8:
                celular = numeros
            else:
                return {
                    'respuesta': (
                        'No pude identificar un número de celular. '
                        'Podés escribirlo (ej: 3814123456) o escribí "enviar" para mandar tu consulta por email sin celular.'
                    ),
                    'intent': 'hablar_con_operador',
                    'acciones': [
                        {'texto': 'Enviar sin celular', 'accion': 'enviar_email_sin_cel'},
                    ],
                    'source': 'hardcoded',
                }

        # Enviar email
        resumen = generar_resumen_email(session)
        email_ok = enviar_email_derivacion(taller, session, resumen, celular or '')

        # Registrar derivación
        Derivacion.objects.create(
            session=session,
            taller=taller,
            canal='email',
            motivo=generar_resumen_conversacion(session),
            celular_cliente=celular or '',
            en_horario=False,
            email_enviado=email_ok,
        )

        nombre = taller.get_nombre()
        if email_ok:
            # Cerrar sesión - la conversación fue derivada a un humano
            session.activa = False
            session.contexto = {}
            session.save(update_fields=['activa', 'contexto'])

            msg = f'✅ ¡Listo! Le enviamos tu consulta al equipo de {nombre}.'
            if celular:
                msg += ' 📱 Incluimos tu celular para que puedan contactarte por WhatsApp.'
            msg += ' Te van a contactar a la brevedad. Esta conversación se cierra, ¡gracias por comunicarte! 😊'
        else:
            # Si falló el email, limpiar contexto pero NO cerrar sesión
            session.contexto = {}
            session.save(update_fields=['contexto'])

            msg = (
                f'⚠️ No pudimos enviar el email en este momento. '
                f'Te sugerimos intentar más tarde o comunicarte directamente '
                f'con {nombre} al {taller.get_telefono() or "teléfono del taller"}.'
            )

        return {
            'respuesta': msg,
            'intent': 'hablar_con_operador',
            'acciones': [],
            'source': 'hardcoded',
        }

    return None


def _procesar_whatsapp(session, taller):
    """Genera respuesta con link de WhatsApp y cierra la sesión"""
    from asistente.models import Derivacion

    nombre = taller.get_nombre()
    whatsapp = taller.get_whatsapp_operador()
    resumen_wa = generar_resumen_conversacion(session, max_chars=200)
    link = generar_link_whatsapp(whatsapp, resumen_wa)

    # Registrar derivación
    Derivacion.objects.create(
        session=session,
        taller=taller,
        canal='whatsapp',
        motivo=generar_resumen_conversacion(session),
        en_horario=True,
    )

    # Cerrar sesión - la conversación fue derivada a un humano
    session.activa = False
    session.contexto = {}
    session.save(update_fields=['activa', 'contexto'])

    return {
        'respuesta': (
            f'📲 Te paso el link para hablar con un operador de {nombre} por WhatsApp. '
            f'Esta conversación se cierra, vas a continuar con un operador humano. ¡Éxitos!'
        ),
        'intent': 'hablar_con_operador',
        'acciones': [
            {'texto': f'💬 Chatear con {nombre}', 'url': link},
        ],
        'source': 'hardcoded',
    }


def _identificar_taller(mensaje, contexto):
    """Intenta identificar qué taller eligió el usuario"""
    from talleres.models import Taller

    # Intentar por accion (seleccionar_planta_X)
    match = re.search(r'seleccionar_planta_(\d+)', mensaje)
    if match:
        pk = int(match.group(1))
        try:
            return Taller.objects.get(pk=pk, status=True)
        except Taller.DoesNotExist:
            pass

    # Intentar por nombre parcial
    talleres = Taller.objects.filter(status=True)
    mensaje_lower = mensaje.lower().strip()
    for taller in talleres:
        nombre = taller.get_nombre().lower()
        if nombre in mensaje_lower or mensaje_lower in nombre:
            return taller

    # Intentar por número (si mandó "1", "2", etc.)
    if mensaje.strip().isdigit():
        idx = int(mensaje.strip()) - 1
        talleres_list = list(talleres)
        if 0 <= idx < len(talleres_list):
            return talleres_list[idx]

    return None


def _extraer_celular(texto):
    """Extrae un número de celular del texto"""
    # Buscar patrones de celular argentino
    limpio = re.sub(r'[\s\-\(\)\+]', '', texto)
    match = re.search(r'(\d{10,13})', limpio)
    if match:
        return match.group(1)
    return None


def enviar_email_sugerencia_revision(sugerencia):
    """
    Envía email al admin/gerente notificando una sugerencia marcada como revisada.
    Incluye botones tokenizados para Implementar o Declinar.
    Retorna (exitoso, mensaje).
    """
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from turnero.utils import get_email_connection
    from asistente.models import AsistenteConfigModel, SugerenciaToken

    config = AsistenteConfigModel.get_config()
    email_destino = config.email_resumen_semanal
    if not email_destino:
        return False, 'No hay email de notificación configurado (email resumen semanal)'

    connection, email_config = get_email_connection()
    if not connection or not email_config:
        return False, 'No hay configuración de email disponible'

    # Crear tokens para las acciones
    token_implementar = SugerenciaToken.objects.create(
        sugerencia=sugerencia, accion='implementar')
    token_declinar = SugerenciaToken.objects.create(
        sugerencia=sugerencia, accion='declinar')

    base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    url_implementar = f"{base_url}/asistente/sugerencia-accion/{token_implementar.token}/"
    url_declinar = f"{base_url}/asistente/sugerencia-accion/{token_declinar.token}/"

    from_email = email_config.default_from_email or email_config.email_host_user
    asunto = f'Sugerencia para revisión - {sugerencia.tema[:60]}'

    # Texto plano
    texto = (
        f"SUGERENCIA DEL ASISTENTE VIRTUAL\n"
        f"{'=' * 40}\n\n"
        f"Tema: {sugerencia.tema}\n"
        f"Categoría: {sugerencia.get_categoria_display()}\n"
        f"Detectada {sugerencia.veces_detectada} vez/veces\n"
        f"Último ejemplo: \"{sugerencia.ultimo_ejemplo[:200]}\"\n\n"
        f"Para tomar una decisión, hacé clic en uno de los siguientes enlaces:\n\n"
        f"IMPLEMENTAR (planificar esta sugerencia):\n{url_implementar}\n\n"
        f"DECLINAR (descartar esta sugerencia):\n{url_declinar}\n\n"
        f"---\nMensaje generado automáticamente por el Asistente Virtual.\n"
    )

    # HTML
    notas_html = ''
    if sugerencia.notas_admin:
        notas_html = f'''
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px 15px; margin: 15px 0; border-radius: 0 4px 4px 0;">
                <p style="margin: 0; font-size: 13px;"><strong>Notas del administrador:</strong> {sugerencia.notas_admin}</p>
            </div>
        '''

    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #003466 0%, #0056b3 100%); padding: 20px 30px; border-radius: 8px 8px 0 0;">
            <h2 style="color: #fff; margin: 0; font-size: 18px;">Sugerencia para Revisión</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0; font-size: 13px;">Asistente Virtual RTV</p>
        </div>
        <div style="background: #fff; padding: 25px 30px; border: 1px solid #e0e0e0;">
            <p style="font-size: 14px; color: #333;">Se marcó una sugerencia como <strong>revisada</strong> y requiere su decisión:</p>

            <div style="background: #f8f9fa; border-left: 4px solid #003466; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                <h3 style="margin: 0 0 8px; color: #003466; font-size: 15px;">{sugerencia.tema}</h3>
                <p style="margin: 4px 0; font-size: 13px; color: #495057;">
                    <strong>Categoría:</strong> {sugerencia.get_categoria_display()}
                </p>
                <p style="margin: 4px 0; font-size: 13px; color: #495057;">
                    <strong>Frecuencia:</strong> detectada {sugerencia.veces_detectada} vez/veces
                </p>
                <p style="margin: 10px 0 0; font-size: 13px; color: #6c757d;">
                    <strong>Ejemplo de consulta:</strong> "{sugerencia.ultimo_ejemplo[:250]}"
                </p>
            </div>

            {notas_html}

            <p style="font-size: 14px; color: #333; margin: 20px 0 15px;">¿Qué desea hacer con esta sugerencia?</p>

            <div style="text-align: center; margin: 25px 0;">
                <a href="{url_implementar}"
                   style="display: inline-block; padding: 12px 28px; background: linear-gradient(135deg, #28a745, #218838);
                          color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;
                          margin: 0 8px 10px;">
                    ✅ Implementar sugerencia
                </a>
                <a href="{url_declinar}"
                   style="display: inline-block; padding: 12px 28px; background: linear-gradient(135deg, #dc3545, #c82333);
                          color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;
                          margin: 0 8px 10px;">
                    ❌ Declinar sugerencia
                </a>
            </div>

            <p style="font-size: 12px; color: #999; text-align: center;">
                Estos enlaces son de uso único y expiran en 30 días.
            </p>
        </div>
        <div style="background: #f8f9fa; padding: 12px 30px; border-radius: 0 0 8px 8px; border: 1px solid #e0e0e0; border-top: none;">
            <p style="margin: 0; font-size: 11px; color: #999; text-align: center;">
                Mensaje generado automáticamente por el Asistente Virtual RTV
            </p>
        </div>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=from_email,
            to=[email_destino],
            connection=connection,
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=False)
        return True, f'Email enviado a {email_destino}'
    except Exception as e:
        return False, f'Error enviando email: {e}'


def enviar_resumen_semanal():
    """
    Envía email semanal con resumen de sugerencias nuevas.
    Retorna (exitoso, mensaje).
    """
    from datetime import timedelta
    from django.core.mail import EmailMultiAlternatives
    from turnero.utils import get_email_connection
    from asistente.models import AsistenteConfigModel, SugerenciaAsistente

    config = AsistenteConfigModel.get_config()
    email_destino = config.email_resumen_semanal
    if not email_destino:
        return False, 'No hay email configurado para el resumen semanal'

    # Sugerencias nuevas o actualizadas en los últimos 7 días
    hace_7_dias = timezone.now() - timedelta(days=7)
    sugerencias = SugerenciaAsistente.objects.filter(
        estado__in=['nueva', 'revisada'],
        updated_at__gte=hace_7_dias,
    ).order_by('-veces_detectada')

    if not sugerencias.exists():
        return False, 'No hay sugerencias nuevas en los últimos 7 días'

    connection, email_config = get_email_connection()
    if not connection or not email_config:
        return False, 'No hay configuración de email disponible'

    from_email = email_config.default_from_email or email_config.email_host_user
    asunto = 'Resumen Semanal - Sugerencias del Asistente Virtual'

    # Texto plano
    texto = "RESUMEN SEMANAL - SUGERENCIAS DEL ASISTENTE VIRTUAL\n"
    texto += "=" * 50 + "\n\n"
    texto += f"Se detectaron {sugerencias.count()} sugerencia(s) en los últimos 7 días:\n\n"

    for i, sug in enumerate(sugerencias, 1):
        texto += f"{i}. {sug.tema} (detectada {sug.veces_detectada} vez/veces)\n"
        texto += f"   Estado: {sug.get_estado_display()}\n"
        if sug.ultimo_ejemplo:
            texto += f"   Ejemplo: \"{sug.ultimo_ejemplo[:150]}\"\n"
        texto += "\n"

    texto += "\nPodés gestionar las sugerencias desde el panel de administración.\n"

    # HTML
    filas_html = ''
    for i, sug in enumerate(sugerencias, 1):
        bg = '#f8f9fa' if i % 2 == 0 else '#fff'
        filas_html += f'''
        <tr style="background:{bg};">
            <td style="padding:10px 14px; font-weight:600; color:#13304D; text-align:center;">{i}</td>
            <td style="padding:10px 14px;">{sug.tema}</td>
            <td style="padding:10px 14px; text-align:center; font-weight:700; color:#003466;">{sug.veces_detectada}</td>
            <td style="padding:10px 14px; font-size:12px; color:#6c757d;">{sug.ultimo_ejemplo[:100] if sug.ultimo_ejemplo else '-'}</td>
            <td style="padding:10px 14px;"><span style="padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; background:#fff3cd; color:#856404;">{sug.get_estado_display()}</span></td>
        </tr>'''

    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #003466 0%, #0056b3 100%); padding: 24px 30px; border-radius: 8px 8px 0 0;">
            <h2 style="color: #fff; margin: 0; font-size: 18px;">Resumen Semanal - Asistente Virtual</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0; font-size: 13px;">Sugerencias detectadas en los últimos 7 días</p>
        </div>
        <div style="background: #fff; padding: 25px 30px; border: 1px solid #e0e0e0;">
            <p>Se detectaron <strong>{sugerencias.count()} sugerencia(s)</strong> nuevas o actualizadas:</p>

            <table style="width:100%; border-collapse:collapse; margin:20px 0; font-size:13px;">
                <thead>
                    <tr style="background:linear-gradient(135deg, #13304D, #1a4066); color:#fff;">
                        <th style="padding:12px 14px; text-align:center; font-size:11px; text-transform:uppercase;">#</th>
                        <th style="padding:12px 14px; text-align:left; font-size:11px; text-transform:uppercase;">Tema</th>
                        <th style="padding:12px 14px; text-align:center; font-size:11px; text-transform:uppercase;">Frecuencia</th>
                        <th style="padding:12px 14px; text-align:left; font-size:11px; text-transform:uppercase;">Ejemplo</th>
                        <th style="padding:12px 14px; text-align:center; font-size:11px; text-transform:uppercase;">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>

            <p style="color: #666; font-size: 13px;">
                Podés gestionar estas sugerencias desde el
                <strong>Panel de Administración &gt; Asistente IA &gt; Sugerencias</strong>.
            </p>
        </div>
        <div style="background: #f8f9fa; padding: 12px 30px; border-radius: 0 0 8px 8px; border: 1px solid #e0e0e0; border-top: none;">
            <p style="margin: 0; font-size: 11px; color: #999; text-align: center;">
                Mensaje generado automáticamente por el Asistente Virtual RTV
            </p>
        </div>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=from_email,
            to=[email_destino],
            connection=connection,
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=False)
        return True, f'Resumen enviado a {email_destino} con {sugerencias.count()} sugerencia(s)'
    except Exception as e:
        return False, f'Error enviando resumen: {e}'
