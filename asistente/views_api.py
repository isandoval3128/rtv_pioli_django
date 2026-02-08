"""
API endpoints públicos del chat (sin login requerido).
"""
import json
import time
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .models import AsistenteConfigModel, ChatSession, ChatMessage
from .services.resolver import resolver_mensaje
from .services.humanizer import humanizar_respuesta


@csrf_exempt
@require_POST
def api_session(request):
    """Crear nueva sesión de chat y retornar mensaje de bienvenida"""
    config = AsistenteConfigModel.get_config()

    if not config.habilitado:
        return JsonResponse({
            'error': 'El asistente no está disponible en este momento.'
        }, status=503)

    # Generar session_key única
    session_key = str(uuid.uuid4())

    # Obtener IP
    ip = _get_client_ip(request)

    # Crear sesión
    session = ChatSession.objects.create(
        session_key=session_key,
        ip_address=ip,
    )

    # Guardar mensaje de bienvenida
    ChatMessage.objects.create(
        session=session,
        rol='assistant',
        contenido=config.mensaje_bienvenida,
        intent='bienvenida',
        source='hardcoded',
    )

    return JsonResponse({
        'session_key': session_key,
        'mensaje': config.mensaje_bienvenida,
        'nombre_asistente': config.nombre_asistente,
    })


@csrf_exempt
@require_POST
def api_mensaje(request):
    """Recibir mensaje del usuario y retornar respuesta del asistente"""
    start_time = time.time()

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    session_key = data.get('session_key')
    mensaje = data.get('mensaje', '').strip()

    if not session_key or not mensaje:
        return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)

    # Obtener sesión
    try:
        session = ChatSession.objects.get(session_key=session_key, activa=True)
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Sesión no encontrada o expirada', 'expirada': True}, status=404)

    # Verificar expiración (24 horas)
    if session.cerrar_si_expirada():
        return JsonResponse({
            'error': 'Tu sesión expiró. Por favor iniciá una nueva conversación.',
            'expirada': True,
        }, status=410)

    # Obtener configuración
    config = AsistenteConfigModel.get_config()
    if not config.habilitado:
        return JsonResponse({
            'error': 'El asistente no está disponible en este momento.'
        }, status=503)

    # Guardar mensaje del usuario
    msg_usuario = ChatMessage.objects.create(
        session=session,
        rol='user',
        contenido=mensaje,
    )

    # Verificar contexto pendiente (flujos conversacionales multi-paso)
    if session.contexto and session.contexto.get('esperando'):
        from .services.escalation import procesar_contexto_pendiente
        resultado_contexto = procesar_contexto_pendiente(session, mensaje)
        if resultado_contexto:
            elapsed_ms = int((time.time() - start_time) * 1000)
            ChatMessage.objects.create(
                session=session,
                rol='assistant',
                contenido=resultado_contexto['respuesta'],
                intent=resultado_contexto.get('intent', ''),
                source=resultado_contexto.get('source', 'hardcoded'),
                tiempo_respuesta_ms=elapsed_ms,
            )
            # Refrescar estado de sesión (pudo cerrarse en la derivación)
            session.refresh_from_db()
            return JsonResponse({
                'respuesta': resultado_contexto['respuesta'],
                'intent': resultado_contexto.get('intent', ''),
                'source': resultado_contexto.get('source', 'hardcoded'),
                'acciones': resultado_contexto.get('acciones', []),
                'session_cerrada': not session.activa,
            })

    # CAPA 1: Resolver datos
    resolver_result = resolver_mensaje(mensaje, session)

    # Manejar derivaciones (resultados especiales del handler)
    if resolver_result.datos and resolver_result.datos.startswith('derivacion_'):
        from .services.escalation import (
            esta_en_horario, _procesar_whatsapp,
            generar_resumen_conversacion, generar_resumen_email,
        )
        from talleres.models import Taller

        partes = resolver_result.datos.split('|')
        tipo_derivacion = partes[0]
        taller_id = int(partes[1])
        taller = Taller.objects.get(pk=taller_id)

        if tipo_derivacion == 'derivacion_whatsapp':
            resultado = _procesar_whatsapp(session, taller)
        else:
            # Fuera de horario: pedir celular
            session.contexto = {
                'esperando': 'celular_cliente',
                'taller_id': taller.pk,
            }
            session.save(update_fields=['contexto'])
            nombre = taller.get_nombre()
            resultado = {
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

        elapsed_ms = int((time.time() - start_time) * 1000)
        ChatMessage.objects.create(
            session=session,
            rol='assistant',
            contenido=resultado['respuesta'],
            intent=resultado.get('intent', ''),
            source=resultado.get('source', 'hardcoded'),
            tiempo_respuesta_ms=elapsed_ms,
        )
        # Refrescar estado de sesión (pudo cerrarse en la derivación WA)
        session.refresh_from_db()
        return JsonResponse({
            'respuesta': resultado['respuesta'],
            'intent': resultado.get('intent', ''),
            'source': resultado.get('source', 'hardcoded'),
            'acciones': resultado.get('acciones', []),
            'session_cerrada': not session.activa,
        })

    # Guardar contexto si el resolver pide selección de planta
    if (resolver_result.acciones
            and any(a.get('accion', '').startswith('seleccionar_planta_') for a in resolver_result.acciones)):
        session.contexto = {
            'esperando': 'seleccion_planta',
            'acciones_previas': resolver_result.acciones,
            'intent_origen': resolver_result.intent,
        }
        session.save(update_fields=['contexto'])

    # CAPA 2: Humanizar respuesta
    humano_result = humanizar_respuesta(resolver_result, config, session)

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Guardar respuesta del asistente
    msg_asistente = ChatMessage.objects.create(
        session=session,
        rol='assistant',
        contenido=humano_result['respuesta'],
        intent=resolver_result.intent,
        source=humano_result['source'],
        faq_usada_id=resolver_result.faq_id,
        tokens_usados=humano_result.get('tokens_usados', 0),
        tiempo_respuesta_ms=elapsed_ms,
    )

    # Acciones: usar las del humanizer si las tiene (ej: derivación por NO_RELEVANTE),
    # sino las del resolver
    acciones = humano_result.get('acciones') or resolver_result.acciones

    return JsonResponse({
        'respuesta': humano_result['respuesta'],
        'intent': resolver_result.intent,
        'source': humano_result['source'],
        'acciones': acciones,
    })


@require_GET
def api_status(request):
    """Estado del asistente (público)"""
    config = AsistenteConfigModel.get_config()
    return JsonResponse({
        'habilitado': config.habilitado,
        'nombre': config.nombre_asistente,
    })


def sugerencia_accion_token(request, token):
    """
    Endpoint público (sin login) para procesar acciones sobre sugerencias
    desde links tokenizados enviados por email.
    """
    from django.http import HttpResponse
    from .models import SugerenciaToken

    try:
        st = SugerenciaToken.objects.select_related('sugerencia').get(token=token)
    except SugerenciaToken.DoesNotExist:
        return HttpResponse(_render_token_page(
            'Token no válido',
            'El enlace que utilizaste no es válido o no existe.',
            'error'
        ), content_type='text/html')

    if st.usado:
        return HttpResponse(_render_token_page(
            'Acción ya procesada',
            f'Esta sugerencia ya fue procesada anteriormente. '
            f'Estado actual: <strong>{st.sugerencia.get_estado_display()}</strong>.',
            'warning'
        ), content_type='text/html')

    if not st.esta_vigente():
        return HttpResponse(_render_token_page(
            'Enlace expirado',
            'Este enlace ha expirado. Por favor, ingresá al panel de administración para gestionar la sugerencia.',
            'error'
        ), content_type='text/html')

    sug = st.sugerencia

    if st.accion == 'implementar':
        sug.estado = 'planificada'
        sug.save(update_fields=['estado'])
        # Marcar todos los tokens de esta sugerencia como usados
        SugerenciaToken.objects.filter(sugerencia=sug).update(usado=True)
        return HttpResponse(_render_token_page(
            'Sugerencia planificada',
            f'La sugerencia <strong>"{sug.tema}"</strong> fue marcada como '
            f'<strong>Planificada</strong>. Podrá implementarla y crear una FAQ desde el panel de administración.',
            'success'
        ), content_type='text/html')

    elif st.accion == 'declinar':
        sug.estado = 'descartada'
        sug.save(update_fields=['estado'])
        # Marcar todos los tokens de esta sugerencia como usados
        SugerenciaToken.objects.filter(sugerencia=sug).update(usado=True)
        return HttpResponse(_render_token_page(
            'Sugerencia descartada',
            f'La sugerencia <strong>"{sug.tema}"</strong> fue marcada como '
            f'<strong>Descartada</strong>.',
            'info'
        ), content_type='text/html')

    return HttpResponse(_render_token_page(
        'Acción no reconocida',
        'La acción solicitada no es válida.',
        'error'
    ), content_type='text/html')


def _render_token_page(titulo, mensaje, tipo='info'):
    """Renderiza una página HTML simple para la respuesta de acciones por token"""
    colores = {
        'success': ('#28a745', '#d4edda', '#155724'),
        'error': ('#dc3545', '#f8d7da', '#721c24'),
        'warning': ('#ffc107', '#fff3cd', '#856404'),
        'info': ('#6c757d', '#e2e3e5', '#383d41'),
    }
    color_header, color_bg, color_text = colores.get(tipo, colores['info'])

    iconos = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
    }
    icono = iconos.get(tipo, '')

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} - RTV Pioli</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; min-height: 100vh;
               display: flex; align-items: center; justify-content: center; padding: 20px; }}
        .card {{ background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                max-width: 500px; width: 100%; overflow: hidden; }}
        .card-header {{ background: linear-gradient(135deg, #003466, #0056b3); padding: 24px 30px;
                       text-align: center; }}
        .card-header h1 {{ color: #fff; font-size: 16px; font-weight: 600; }}
        .card-header p {{ color: rgba(255,255,255,0.7); font-size: 12px; margin-top: 4px; }}
        .card-body {{ padding: 30px; text-align: center; }}
        .icono {{ font-size: 48px; margin-bottom: 16px; }}
        .titulo {{ font-size: 20px; font-weight: 700; color: #333; margin-bottom: 12px; }}
        .mensaje {{ font-size: 14px; color: #555; line-height: 1.6;
                   background: {color_bg}; color: {color_text}; padding: 16px; border-radius: 8px; }}
        .footer {{ padding: 16px 30px; text-align: center; border-top: 1px solid #eee; }}
        .footer p {{ font-size: 11px; color: #999; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="card-header">
            <h1>Asistente Virtual RTV</h1>
            <p>Gestión de Sugerencias</p>
        </div>
        <div class="card-body">
            <div class="icono">{icono}</div>
            <div class="titulo">{titulo}</div>
            <div class="mensaje">{mensaje}</div>
        </div>
        <div class="footer">
            <p>RTV Pioli - Asistente Virtual</p>
        </div>
    </div>
</body>
</html>"""


def _get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
