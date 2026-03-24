"""
Capa 2: Humanizador de respuestas con IA.
Toma los datos resueltos por Capa 1 y los presenta de forma natural y humana.
"""
import logging

from .ai_provider import get_ai_client
from .resolver import ResolverResult

logger = logging.getLogger(__name__)


def humanizar_respuesta(resolver_result, config, session=None):
    """
    Toma el resultado del resolver y genera una respuesta humanizada.

    Args:
        resolver_result: ResolverResult del resolver
        config: AsistenteConfigModel
        session: ChatSession (opcional, para contexto y logging)

    Returns:
        dict con: respuesta, source, tokens_usados, tiempo_ms, uso_ia
    """
    result = {
        'respuesta': '',
        'source': resolver_result.source,
        'tokens_usados': 0,
        'tiempo_ms': 0,
        'uso_ia': False,
    }

    # 1. Si hay respuesta fija, devolver directo (sin IA)
    if resolver_result.respuesta_fija:
        result['respuesta'] = resolver_result.respuesta_fija
        return result

    # 2. Si necesita humanizar datos concretos → prompt corto a la IA
    if resolver_result.necesita_humanizar and resolver_result.datos:
        return _humanizar_datos(resolver_result, config, session)

    # 3. Si necesita IA completa (no se pudo resolver por keywords/DB)
    if resolver_result.necesita_ia_completa:
        return _respuesta_ia_completa(resolver_result, config, session)

    # Fallback
    result['respuesta'] = config.mensaje_error
    return result


def _humanizar_datos(resolver_result, config, session=None):
    """Humaniza datos concretos con un prompt corto"""
    result = {
        'respuesta': '',
        'source': resolver_result.source,
        'tokens_usados': 0,
        'tiempo_ms': 0,
        'uso_ia': True,
        'acciones': [],
    }

    # Verificar límites de IA
    if not _verificar_limites(config, session):
        result['respuesta'] = resolver_result.datos
        result['uso_ia'] = False
        return result

    try:
        ai_client = get_ai_client(config)

        prompt = (
            f"Sos un asistente virtual de una empresa de Revisión Técnica Vehicular.\n"
            f"El usuario preguntó: \"{resolver_result.pregunta_original}\"\n\n"
            f"Se encontró la siguiente información en el sistema:\n{resolver_result.datos}\n\n"
            f"INSTRUCCIONES:\n"
            f"- Si la información responde lo que el usuario preguntó, "
            f"reformulala de manera natural, amable y concisa en español argentino. "
            f"Usá máximo 2-3 oraciones de texto introductorio. NO inventes datos.\n"
            f"- CRITICO: Los números, precios y montos deben copiarse EXACTAMENTE como aparecen "
            f"en los datos. NO redondees, NO modifiques, NO inventes cifras. "
            f"Si dice $50,000.00 respondé $50,000, si dice $240,000.00 respondé $240,000. "
            f"Alterarlos es un error grave.\n"
            f"- Si los datos contienen una lista (tarifas, horarios, ubicaciones, etc.), "
            f"incluí TODOS los items de la lista. No resumas ni omitas elementos.\n"
            f"- FORMATO DE RESPUESTA: Usá texto plano con estos formatos:\n"
            f"  · **texto** para negritas (nombres, títulos, precios importantes)\n"
            f"  · Listas con guión: cada ítem en su propia línea empezando con '- '\n"
            f"  · Saltos de línea para separar secciones\n"
            f"  · Emojis relevantes (1-2 máximo): 🚗 vehículos, 📋 turnos, 💰 tarifas, 📍 ubicación, ✅ confirmaciones\n"
            f"  · NO uses HTML, solo texto plano con los formatos indicados\n"
            f"- Si la información NO es relevante para lo que el usuario pidió, "
            f"respondé SOLO con la palabra: NO_RELEVANTE\n"
            f"- Si la consulta requiere atención personalizada (reclamos, copias de comprobantes, "
            f"problemas con pagos, rectificaciones, trámites que no se resuelven con esta info), "
            f"respondé SOLO con la palabra: NECESITA_OPERADOR"
        )

        context = {
            'system_prompt': config.system_prompt,
            'session': session,
        }

        ai_result = ai_client.generate_response(prompt, context)

        if ai_result['exitoso']:
            respuesta = ai_result['respuesta'].strip()
            result['tokens_usados'] = ai_result['tokens_input'] + ai_result['tokens_output']
            result['tiempo_ms'] = ai_result['latencia_ms']

            # Actualizar contador de IA en sesión
            if session:
                from asistente.models import ChatSession
                ChatSession.objects.filter(pk=session.pk).update(
                    ai_calls_count=session.ai_calls_count + 1
                )

            # Detectar si necesita operador humano
            if 'NECESITA_OPERADOR' in respuesta:
                result['respuesta'] = (
                    '😕 Entiendo tu consulta, pero necesitás atención personalizada '
                    'para poder resolverla. Si querés, puedo derivarte con un operador.'
                )
                result['source'] = 'hardcoded'
                result['acciones'] = [
                    {'texto': '👤 Hablar con un operador', 'accion': 'quiero hablar con un operador'},
                ]
                return result

            # Detectar si la IA determinó que los datos no son relevantes
            if 'NO_RELEVANTE' in respuesta:
                # La IA (con system prompt de RTV) determinó que la pregunta
                # no es relevante → fuera de dominio (falso positivo de keywords)
                result['respuesta'] = (
                    'Disculpá, solo puedo ayudarte con temas relacionados '
                    'a la Revisión Técnica Vehicular: turnos, tarifas, '
                    'ubicación y servicios. ¿Tenés alguna consulta sobre estos temas?'
                )
                result['source'] = 'hardcoded'
            else:
                result['respuesta'] = respuesta
                # Cachear respuesta
                _cachear_respuesta(resolver_result, result['respuesta'])
        else:
            # Fallback: devolver datos sin humanizar
            result['respuesta'] = resolver_result.datos
            result['uso_ia'] = False
            logger.warning(f"Humanización falló, devolviendo datos crudos: {ai_result['error']}")

    except Exception as e:
        result['respuesta'] = resolver_result.datos
        result['uso_ia'] = False
        logger.error(f"Error en humanización: {e}")

    return result


def _respuesta_ia_completa(resolver_result, config, session=None):
    """Genera respuesta completa con IA cuando no se pudo resolver localmente"""
    result = {
        'respuesta': '',
        'source': 'ai',
        'tokens_usados': 0,
        'tiempo_ms': 0,
        'uso_ia': True,
        'acciones': [],
    }

    # Verificar límites
    if not _verificar_limites(config, session):
        result['respuesta'] = config.mensaje_error
        result['uso_ia'] = False
        return result

    try:
        ai_client = get_ai_client(config)

        # Construir prompt base
        prompt = (
            f"{config.system_prompt}\n\n"
            f"Si la consulta NO está relacionada con revisión técnica vehicular, turnos, "
            f"tarifas, ubicación o servicios de RTV, respondé SOLO con la palabra: NO_RELEVANTE\n\n"
            f"Si la consulta SÍ está relacionada con RTV pero requiere atención personalizada "
            f"(reclamos, copias de comprobantes, problemas con pagos, rectificaciones, trámites "
            f"específicos que no podés resolver con la información disponible), respondé SOLO con "
            f"la palabra: NECESITA_OPERADOR\n\n"
        )

        # Inyectar contexto KB si hay fragmentos relevantes
        if resolver_result.contexto_kb:
            contexto_docs = "\n\n".join([
                f"[Documento: {frag['titulo']}]\n{frag['texto']}"
                for frag in resolver_result.contexto_kb
            ])
            prompt += (
                f"INFORMACIÓN DE LA BASE DE CONOCIMIENTO:\n{contexto_docs}\n\n"
                f"Usá la información anterior para responder la consulta del cliente. "
                f"Si la información no es suficiente para una respuesta completa, indicalo amablemente.\n\n"
            )

        prompt += (
            f"Consulta del usuario: \"{resolver_result.datos}\"\n\n"
            f"Si podés responder, hacelo de forma natural, amable y concisa en español argentino.\n"
            f"FORMATO: Usá texto plano con **negritas**, listas con '- ' y saltos de línea para estructurar. "
            f"Usá 1-2 emojis relevantes (🚗 vehículos, 📋 turnos, 💰 tarifas, 📍 ubicación). "
            f"NO uses HTML."
        )

        context = {
            'system_prompt': config.system_prompt,
            'session': session,
        }

        ai_result = ai_client.generate_response(prompt, context)

        if ai_result['exitoso']:
            respuesta = ai_result['respuesta'].strip()
            result['tokens_usados'] = ai_result['tokens_input'] + ai_result['tokens_output']
            result['tiempo_ms'] = ai_result['latencia_ms']

            # Actualizar contador
            if session:
                from asistente.models import ChatSession
                ChatSession.objects.filter(pk=session.pk).update(
                    ai_calls_count=session.ai_calls_count + 1
                )

            # Detectar si necesita operador humano
            if 'NECESITA_OPERADOR' in respuesta:
                result['respuesta'] = (
                    '😕 Entiendo tu consulta, pero necesitás atención personalizada '
                    'para poder resolverla. Si querés, puedo derivarte con un operador.'
                )
                result['source'] = 'hardcoded'
                result['acciones'] = [
                    {'texto': '👤 Hablar con un operador', 'accion': 'quiero hablar con un operador'},
                ]
                _registrar_sugerencia(resolver_result.datos, session)
                return result

            # Detectar si la IA no pudo responder
            if 'NO_RELEVANTE' in respuesta:
                # Diferenciar: fuera de dominio vs tema RTV sin info
                es_fuera_de_dominio = resolver_result.intent in (
                    'desconocido', 'kb', '', None
                ) and resolver_result.source in ('needs_ai', 'kb+ai')

                if es_fuera_de_dominio:
                    # Fuera de dominio total: NO ofrecer operador
                    result['respuesta'] = (
                        'Disculpá, solo puedo ayudarte con temas relacionados '
                        'a la Revisión Técnica Vehicular: turnos, tarifas, '
                        'ubicación y servicios. ¿Tenés alguna consulta sobre estos temas?'
                    )
                    result['source'] = 'hardcoded'
                else:
                    # Tema RTV pero sin info suficiente: ofrecer operador
                    result['respuesta'] = (
                        '😕 En este momento no cuento con esa información para ayudarte. '
                        'Si querés, puedo derivarte con un operador para que te asista personalmente.'
                    )
                    result['source'] = 'hardcoded'
                    result['acciones'] = [
                        {'texto': '👤 Hablar con un operador', 'accion': 'quiero hablar con un operador'},
                    ]
                _registrar_sugerencia(resolver_result.datos, session)
            else:
                result['respuesta'] = respuesta
                # Sugerir como FAQ si la respuesta fue exitosa
                _sugerir_faq(resolver_result.datos, respuesta, resolver_result.intent)

                # Registrar sugerencia si es consulta no resuelta o fuera de dominio
                if resolver_result.intent in ('desconocido', 'fuera_dominio', ''):
                    _registrar_sugerencia(resolver_result.datos, session)
        else:
            result['respuesta'] = config.mensaje_error
            result['uso_ia'] = False

    except Exception as e:
        result['respuesta'] = config.mensaje_error
        result['uso_ia'] = False
        logger.error(f"Error en respuesta IA completa: {e}")

    return result


def _verificar_limites(config, session):
    """Verifica si se pueden hacer más llamadas a la IA"""
    from asistente.models import AIUsageLog
    from django.utils import timezone
    from datetime import timedelta

    # Límite por sesión
    if session and session.ai_calls_count >= config.max_ai_calls_per_session:
        logger.warning(f"Límite de IA por sesión alcanzado: {session.session_key}")
        return False

    # Límite diario
    hoy = timezone.localdate()
    calls_hoy = AIUsageLog.objects.filter(
        created_at__date=hoy, exitoso=True
    ).count()
    if calls_hoy >= config.max_ai_calls_per_day:
        logger.warning(f"Límite diario de IA alcanzado: {calls_hoy}/{config.max_ai_calls_per_day}")
        return False

    return True


def _cachear_respuesta(resolver_result, respuesta):
    """Cachea la respuesta humanizada para reutilizar"""
    from asistente.models import CachedResponse
    from .intents import normalizar_texto

    try:
        CachedResponse.objects.create(
            pregunta_normalizada=normalizar_texto(resolver_result.datos)[:500],
            intent=resolver_result.intent,
            datos_contexto={'datos': resolver_result.datos[:1000]},
            respuesta=respuesta,
        )
    except Exception as e:
        logger.error(f"Error cacheando respuesta: {e}")


def _corregir_ortografia(texto):
    """Corrige ortografía y redacción del texto usando IA antes de guardarlo como sugerencia"""
    from asistente.models import AsistenteConfigModel

    try:
        config = AsistenteConfigModel.get_config()
        from django.conf import settings
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or config.ai_api_key
        if not api_key:
            return texto

        ai_client = get_ai_client(config)
        prompt = (
            f"Corregí la ortografía y redacción del siguiente texto. "
            f"Devolvé SOLO el texto corregido, sin explicaciones ni comillas:\n\n"
            f"{texto}"
        )
        result = ai_client.generate_response(prompt, {'system_prompt': '', 'session': None})
        if result['exitoso']:
            corregido = result['respuesta'].strip().strip('"\'')
            if corregido and len(corregido) < len(texto) * 3:
                return corregido
    except Exception as e:
        logger.debug(f"No se pudo corregir ortografía: {e}")

    return texto


def _registrar_sugerencia(texto, session=None):
    """Registra o actualiza una sugerencia basada en consulta no resuelta"""
    from asistente.models import SugerenciaAsistente
    from .intents import normalizar_texto
    from .resolver import _similitud_basica

    try:
        texto_norm = normalizar_texto(texto)[:200]

        # Buscar existente por similitud
        sugerencias = SugerenciaAsistente.objects.filter(estado__in=['nueva', 'revisada'])
        for sug in sugerencias:
            if _similitud_basica(sug.tema_normalizado, texto_norm) > 0.6:
                SugerenciaAsistente.objects.filter(pk=sug.pk).update(
                    veces_detectada=sug.veces_detectada + 1,
                    ultimo_ejemplo=texto[:500],
                    session_ejemplo=session,
                )
                return

        # Corregir ortografía antes de guardar nueva sugerencia
        tema_corregido = _corregir_ortografia(texto)

        # Crear nueva
        SugerenciaAsistente.objects.create(
            tema=tema_corregido[:200],
            tema_normalizado=normalizar_texto(tema_corregido)[:200],
            ultimo_ejemplo=texto[:500],
            session_ejemplo=session,
        )
    except Exception as e:
        logger.error(f"Error registrando sugerencia: {e}")


def _sugerir_faq(pregunta, respuesta, intent):
    """Crea una FAQ sugerida (no aprobada) a partir de una respuesta exitosa de IA"""
    from asistente.models import FAQ

    try:
        # No crear duplicados
        if FAQ.objects.filter(pregunta__iexact=pregunta[:500]).exists():
            return

        FAQ.objects.create(
            pregunta=pregunta[:500],
            respuesta_datos=respuesta,
            categoria=intent if intent in dict(FAQ.CATEGORIA_CHOICES) else 'general',
            origen='sugerida_ia',
            aprobada=False,
        )
    except Exception as e:
        logger.error(f"Error sugiriendo FAQ: {e}")
