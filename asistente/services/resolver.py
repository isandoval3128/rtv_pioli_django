"""
Capa 1: Resolver de datos (sin IA).
Determina QUÉ datos responder basándose en el intent detectado.
Flujo: saludo? → FAQ match? → intent DB? → necesita IA
"""
import random
import re
from dataclasses import dataclass, field
from typing import Optional

from .intents import (
    INTENTS, RESPUESTAS_FIJAS,
    detectar_intent_por_keywords, normalizar_texto,
)


@dataclass
class ResolverResult:
    """Resultado del resolver"""
    intent: str = ''
    datos: str = ''
    source: str = ''  # faq, cache, db, hardcoded, needs_ai
    respuesta_fija: Optional[str] = None
    necesita_humanizar: bool = False
    necesita_ia_completa: bool = False
    faq_id: Optional[int] = None
    acciones: list = field(default_factory=list)
    confidence: float = 0.0
    pregunta_original: str = ''  # Pregunta original del usuario
    contexto_kb: list = field(default_factory=list)  # Fragmentos de Base de Conocimiento


def resolver_mensaje(texto, session=None):
    """
    Punto de entrada principal del resolver.
    Analiza el texto y retorna datos sin usar IA.

    Pipeline:
    1. Detectar intent
    2. Intents fijos (saludo, despedida) - con detección de mensaje compuesto
    3. Intents prioritarios (hablar_con_operador) - bypass FAQ
    4. FAQ search
    5. Cache search
    6. DB handlers
    7. KB search
    8. IA completa (fallback)
    """
    texto_norm = normalizar_texto(texto)

    # 1. Detectar intent por keywords
    intent, confidence = detectar_intent_por_keywords(texto)

    # 2. Si es un intent fijo (saludo, despedida, etc.) → respuesta directa
    #    PERO: si el mensaje es compuesto ("Hola, cuánto cuesta..."),
    #    intentar detectar un intent de DB más específico
    if intent and INTENTS.get(intent, {}).get('tipo') == 'fijo':
        palabras = texto_norm.split()
        if len(palabras) > 4:
            # Mensaje largo: puede ser saludo + consulta real
            intent_db, conf_db = _detectar_mejor_intent_db(texto)
            if intent_db and conf_db >= 0.33:
                intent = intent_db
                confidence = conf_db
                # Continúa al paso 3 con el intent de DB
            else:
                respuestas = RESPUESTAS_FIJAS.get(intent, ['Hola, ¿en qué puedo ayudarte?'])
                return ResolverResult(
                    intent=intent,
                    respuesta_fija=random.choice(respuestas),
                    source='hardcoded',
                    confidence=confidence,
                    pregunta_original=texto,
                )
        else:
            respuestas = RESPUESTAS_FIJAS.get(intent, ['Hola, ¿en qué puedo ayudarte?'])
            return ResolverResult(
                intent=intent,
                respuesta_fija=random.choice(respuestas),
                source='hardcoded',
                confidence=confidence,
                pregunta_original=texto,
            )

    # 3. Intents prioritarios: van DIRECTO al handler (sin pasar por FAQ)
    #    Esto evita que FAQs genéricas intercepten flujos con lógica especial
    INTENTS_PRIORITARIOS = {'hablar_con_operador', 'reprogramar_turno', 'cancelar_turno'}
    if intent in INTENTS_PRIORITARIOS and INTENTS.get(intent, {}).get('handler'):
        # Si la confianza es baja (posible typo), confirmar antes de ejecutar
        if confidence < 0.6:
            CONFIRMACIONES = {
                'cancelar_turno': {
                    'pregunta': '¿Querés cancelar un turno?',
                    'si_texto': '✅ Sí, cancelar turno',
                    'si_accion': 'quiero cancelar mi turno',
                },
                'reprogramar_turno': {
                    'pregunta': '¿Querés reprogramar un turno?',
                    'si_texto': '✅ Sí, reprogramar turno',
                    'si_accion': 'quiero reprogramar mi turno',
                },
                'hablar_con_operador': {
                    'pregunta': '¿Querés hablar con un operador?',
                    'si_texto': '✅ Sí, hablar con operador',
                    'si_accion': 'quiero hablar con un operador',
                },
            }
            conf = CONFIRMACIONES.get(intent)
            if conf:
                return ResolverResult(
                    intent=intent,
                    respuesta_fija=f"🤔 Disculpá, no entendí bien. {conf['pregunta']}",
                    source='hardcoded',
                    confidence=confidence,
                    pregunta_original=texto,
                    acciones=[
                        {'texto': conf['si_texto'], 'accion': conf['si_accion']},
                        {'texto': '❌ No, otra consulta', 'accion': 'no gracias, otra consulta'},
                    ],
                )

        handler_name = INTENTS[intent]['handler']
        handler = HANDLERS.get(handler_name)
        if handler:
            result = handler(texto, intent, confidence)
            result.pregunta_original = texto
            return result

    # 3b. Si hay código de turno TRN-XXXXXX, forzar handler DB correspondiente
    if re.search(r'TRN-[A-Fa-f0-9]{4,}', texto.upper()):
        # Si el intent ya es reprogramar o cancelar, usar ESE handler (no consulta)
        if intent in ('reprogramar_turno', 'cancelar_turno'):
            handler_name = INTENTS[intent]['handler']
        else:
            handler_name = 'resolver_consulta_turno'
            intent = 'consultar_turno'
        handler = HANDLERS.get(handler_name)
        if handler:
            result = handler(texto, intent, max(confidence, 0.9))
            result.pregunta_original = texto
            return result

    # 3c. Si el mensaje parece una patente argentina suelta, forzar handler de turno
    #     Formatos: ABC123 (viejo), AB123CD (Mercosur)
    texto_limpio = re.sub(r'[\s\-.]', '', texto.strip()).upper()
    if re.match(r'^[A-Z]{2,3}\d{3}[A-Z]{0,3}$', texto_limpio) and len(texto_limpio) in (6, 7):
        handler = HANDLERS.get('resolver_consulta_turno')
        if handler:
            result = handler(texto, 'consultar_turno', 0.8)
            result.pregunta_original = texto
            return result

    # 4. Buscar en FAQs
    faq_result = _buscar_faq(texto_norm)
    if faq_result:
        faq_result.pregunta_original = texto
        return faq_result

    # 5. Buscar en cache de respuestas
    cache_result = _buscar_cache(texto_norm, intent)
    if cache_result:
        cache_result.pregunta_original = texto
        return cache_result

    # 6. Si hay intent con handler, resolver datos desde DB
    if intent and INTENTS.get(intent, {}).get('handler'):
        handler_name = INTENTS[intent]['handler']
        handler = HANDLERS.get(handler_name)
        if handler:
            result = handler(texto, intent, confidence)
            result.pregunta_original = texto
            return result

    # 7. Buscar en Base de Conocimiento (KB)
    from .kb_service import buscar_en_kb
    fragmentos_kb = buscar_en_kb(texto)
    if fragmentos_kb:
        return ResolverResult(
            intent=intent or 'kb',
            datos=texto,
            source='kb+ai',
            necesita_ia_completa=True,
            confidence=confidence,
            pregunta_original=texto,
            contexto_kb=fragmentos_kb,
        )

    # 8. No se pudo resolver → necesita IA completa
    return ResolverResult(
        intent=intent or 'desconocido',
        datos=texto,
        source='needs_ai',
        necesita_ia_completa=True,
        confidence=confidence,
        pregunta_original=texto,
    )


def _detectar_mejor_intent_db(texto):
    """
    Detecta el mejor intent de tipo 'db' ignorando los fijos (saludo, etc).
    Se usa cuando el mensaje parece compuesto ("Hola, cuánto cuesta...")
    """
    texto_normalizado = normalizar_texto(texto)
    palabras_texto = set(texto_normalizado.split())
    mejor_intent = None
    mejor_score = 0

    for intent_name, intent_data in INTENTS.items():
        if intent_data.get('tipo') != 'db':
            continue
        score = 0
        for keyword in intent_data['keywords']:
            keyword_norm = normalizar_texto(keyword)

            if keyword_norm in texto_normalizado:
                if texto_normalizado == keyword_norm:
                    score += 3
                elif texto_normalizado.startswith(keyword_norm):
                    score += 2
                else:
                    score += 1
            elif ' ' in keyword_norm:
                kw_words = set(keyword_norm.split())
                matches = kw_words & palabras_texto
                if len(matches) == len(kw_words):
                    score += 1.5

        if score > mejor_score:
            mejor_score = score
            mejor_intent = intent_name

    confidence = min(mejor_score / 3.0, 1.0) if mejor_score > 0 else 0
    return mejor_intent, confidence


def _buscar_faq(texto_norm):
    """Busca coincidencia en FAQs por palabras clave"""
    from asistente.models import FAQ

    faqs = FAQ.objects.filter(aprobada=True, status=True)
    mejor_faq = None
    mejor_score = 0

    for faq in faqs:
        score = 0
        keywords = faq.palabras_clave or []
        for kw in keywords:
            kw_norm = normalizar_texto(kw)
            if kw_norm in texto_norm:
                score += 1

        # También comparar con la pregunta
        pregunta_norm = normalizar_texto(faq.pregunta)
        palabras_pregunta = pregunta_norm.split()
        for palabra in palabras_pregunta:
            if len(palabra) > 3 and palabra in texto_norm:
                score += 0.5

        if score > mejor_score and score >= 1:
            mejor_score = score
            mejor_faq = faq

    if mejor_faq:
        # Incrementar contador
        FAQ.objects.filter(pk=mejor_faq.pk).update(veces_usada=mejor_faq.veces_usada + 1)

        # Si tiene respuesta humanizada cacheada, usarla directo
        if mejor_faq.respuesta_humanizada:
            return ResolverResult(
                intent=mejor_faq.categoria,
                datos=mejor_faq.respuesta_datos,
                respuesta_fija=mejor_faq.respuesta_humanizada,
                source='faq',
                faq_id=mejor_faq.pk,
                confidence=min(mejor_score / 2.0, 1.0),
            )

        # Si no, necesita humanizar los datos
        return ResolverResult(
            intent=mejor_faq.categoria,
            datos=mejor_faq.respuesta_datos,
            source='faq',
            necesita_humanizar=True,
            faq_id=mejor_faq.pk,
            confidence=min(mejor_score / 2.0, 1.0),
        )

    return None


def _buscar_cache(texto_norm, intent):
    """Busca en cache de respuestas"""
    from asistente.models import CachedResponse

    if not intent:
        return None

    # Buscar cache exacto o similar
    caches = CachedResponse.objects.filter(intent=intent, vigente=True)
    for cache in caches:
        cache_norm = normalizar_texto(cache.pregunta_normalizada)
        if cache_norm == texto_norm or _similitud_basica(cache_norm, texto_norm) > 0.8:
            CachedResponse.objects.filter(pk=cache.pk).update(veces_usada=cache.veces_usada + 1)
            return ResolverResult(
                intent=intent,
                datos=str(cache.datos_contexto),
                respuesta_fija=cache.respuesta,
                source='cache',
                confidence=0.9,
            )

    return None


def _similitud_basica(texto1, texto2):
    """Similitud básica basada en palabras compartidas"""
    palabras1 = set(texto1.split())
    palabras2 = set(texto2.split())
    if not palabras1 or not palabras2:
        return 0
    interseccion = palabras1 & palabras2
    union = palabras1 | palabras2
    return len(interseccion) / len(union)


# ==========================================
# HANDLERS: Resuelven datos desde la DB
# ==========================================

def resolver_tarifas(texto, intent, confidence):
    """Resuelve tarifas desde TipoVehiculo"""
    from talleres.models import TipoVehiculo

    tipos = TipoVehiculo.objects.filter(status=True).order_by('nombre')
    if not tipos.exists():
        return ResolverResult(
            intent=intent,
            datos='No hay tarifas disponibles actualmente.',
            source='db',
            necesita_humanizar=True,
            confidence=confidence,
        )

    datos_tarifas = []
    for tipo in tipos:
        precios = []
        if tipo.precio_provincial:
            precios.append(f"Provincial: ${tipo.precio_provincial:,.0f}")
        if tipo.precio_nacional:
            precios.append(f"Nacional: ${tipo.precio_nacional:,.0f}")
        if tipo.precio_cajutad:
            precios.append(f"CAJUTAC: ${tipo.precio_cajutad:,.0f}")
        precio_str = ' | '.join(precios) if precios else 'Consultar'
        datos_tarifas.append(f"- {tipo.nombre}: {precio_str}")

    datos = "Tarifas de trámites RTV:\n" + "\n".join(datos_tarifas)

    return ResolverResult(
        intent=intent,
        datos=datos,
        source='db',
        necesita_humanizar=True,
        confidence=confidence,
        acciones=[
            {'texto': 'Ver tarifas completas', 'scroll_to': '#tarifas'},
            {'texto': 'Sacar turno', 'url': '/turnero/paso1/'},
        ],
    )


def _info_turno_con_estado(turno):
    """Genera info del turno con detección de vencimiento y acciones relevantes."""
    from django.utils import timezone

    hoy = timezone.now().date()
    acciones = []

    datos = (
        f"Turno {turno.codigo}:\n"
        f"- Estado: {turno.get_estado_display()}\n"
        f"- Fecha: {turno.fecha.strftime('%d/%m/%Y')}\n"
        f"- Hora: {turno.hora_inicio.strftime('%H:%M')} a {turno.hora_fin.strftime('%H:%M')}\n"
        f"- Vehículo: {turno.vehiculo.dominio}\n"
        f"- Taller: {turno.taller.get_nombre()}\n"
        f"- Trámite: {turno.tipo_vehiculo.nombre}"
    )

    # Detectar turno vencido (fecha pasada + estado aún pendiente/confirmado)
    if turno.fecha < hoy and turno.estado in ('PENDIENTE', 'CONFIRMADO'):
        datos += (
            f"\n\n⚠️ ATENCIÓN: Este turno era para el {turno.fecha.strftime('%d/%m/%Y')} "
            f"y ya pasó la fecha. Si no asististe, podés sacar un nuevo turno."
        )
        acciones = [{'texto': '📅 Sacar nuevo turno', 'url': '/turnero/paso1/'}]
    elif turno.fecha == hoy and turno.estado in ('PENDIENTE', 'CONFIRMADO'):
        datos += "\n\n📌 Tu turno es HOY. ¡Recordá asistir con la documentación necesaria!"
    elif turno.estado in ('PENDIENTE', 'CONFIRMADO') and turno.fecha > hoy:
        if turno.puede_reprogramar:
            acciones.append({'texto': '🔄 Reprogramar', 'accion': f'quiero reprogramar el turno {turno.codigo}'})
        if turno.puede_cancelar:
            acciones.append({'texto': '❌ Cancelar turno', 'accion': f'quiero cancelar el turno {turno.codigo}'})
        if not acciones:
            acciones = [{'texto': '📋 Gestionar turno', 'url': '/turnero/consultar/'}]

    return datos, acciones


def resolver_consulta_turno(texto, intent, confidence):
    """Resuelve consulta de turno por código o dominio"""
    from turnero.models import Turno

    # Buscar código de turno (TRN-XXXXXX)
    codigo_match = re.search(r'TRN-[A-Fa-f0-9]{6}', texto.upper())
    if codigo_match:
        codigo = codigo_match.group()
        try:
            turno = Turno.objects.select_related(
                'vehiculo', 'taller', 'tipo_vehiculo', 'cliente'
            ).get(codigo=codigo)

            datos, acciones = _info_turno_con_estado(turno)
            return ResolverResult(
                intent=intent, datos=datos, source='db',
                necesita_humanizar=True, confidence=1.0,
                acciones=acciones,
            )
        except Turno.DoesNotExist:
            return ResolverResult(
                intent=intent,
                datos=f'No se encontró un turno con el código {codigo}.',
                source='db', necesita_humanizar=True, confidence=confidence,
            )

    # Buscar por dominio/patente
    dominio_match = re.search(r'[A-Za-z]{2,3}\d{3}[A-Za-z]{0,3}', texto.upper())
    if dominio_match:
        dominio = dominio_match.group().upper()
        from django.utils import timezone
        hoy = timezone.now().date()

        # Buscar turnos pendientes/confirmados (incluir vencidos para avisar)
        turnos = Turno.objects.filter(
            vehiculo__dominio__iexact=dominio,
            estado__in=['PENDIENTE', 'CONFIRMADO']
        ).select_related('vehiculo', 'taller', 'tipo_vehiculo').order_by('fecha')[:3]

        if turnos:
            # Separar futuros/hoy de vencidos
            futuros = [t for t in turnos if t.fecha >= hoy]
            vencidos = [t for t in turnos if t.fecha < hoy]

            datos = f"Turnos para vehículo {dominio}:\n"
            for t in futuros:
                etiqueta_hoy = " (HOY)" if t.fecha == hoy else ""
                datos += (
                    f"- {t.codigo}: {t.fecha.strftime('%d/%m/%Y')}{etiqueta_hoy} a las "
                    f"{t.hora_inicio.strftime('%H:%M')} en {t.taller.get_nombre()} "
                    f"({t.get_estado_display()})\n"
                )
            for t in vencidos:
                datos += (
                    f"- {t.codigo}: {t.fecha.strftime('%d/%m/%Y')} en {t.taller.get_nombre()} "
                    f"(⚠️ VENCIDO - no asistido)\n"
                )

            acciones = []
            if futuros:
                if len(futuros) == 1:
                    t = futuros[0]
                    if t.puede_reprogramar:
                        acciones.append({'texto': '🔄 Reprogramar', 'accion': f'quiero reprogramar el turno {t.codigo}'})
                    if t.puede_cancelar:
                        acciones.append({'texto': '❌ Cancelar turno', 'accion': f'quiero cancelar el turno {t.codigo}'})
                if not acciones:
                    acciones.append({'texto': '📋 Gestionar turno', 'url': '/turnero/consultar/'})
            if vencidos and not futuros:
                datos += "\nTus turnos están vencidos. Podés sacar uno nuevo."
                acciones.append({'texto': '📅 Sacar nuevo turno', 'url': '/turnero/paso1/'})

            return ResolverResult(
                intent=intent, datos=datos, source='db',
                necesita_humanizar=True, confidence=0.9,
                acciones=acciones,
            )
        else:
            # Patente reconocida pero sin turnos activos
            return ResolverResult(
                intent=intent,
                datos=(
                    f'No se encontraron turnos activos para el vehículo {dominio}.\n\n'
                    'Si tenés un turno, puede que ya haya sido completado o cancelado.\n'
                    'Podés sacar un nuevo turno online.'
                ),
                source='db', necesita_humanizar=True, confidence=0.9,
                acciones=[
                    {'texto': '📅 Sacar nuevo turno', 'url': '/turnero/paso1/'},
                    {'texto': '📋 Consultar en la web', 'url': '/turnero/consultar/'},
                ],
            )

    # No se encontró referencia específica → guiar al usuario con formatos claros
    return ResolverResult(
        intent=intent,
        datos=(
            'Para consultar un turno necesito uno de estos datos:\n'
            '- Código de turno (formato: TRN-A1B2C3) — lo recibiste por email al reservar\n'
            '- Patente del vehículo (formato: ABC123 o AB123CD)\n\n'
            'Podés escribirlo directamente acá y lo busco.'
        ),
        source='db', necesita_humanizar=True, confidence=confidence,
        acciones=[
            {'texto': '📋 Consultar en la web', 'url': '/turnero/consultar/'},
        ],
    )


def resolver_crear_turno(texto, intent, confidence):
    """Guía al usuario para crear un turno"""
    from talleres.models import Taller
    talleres = Taller.objects.filter(status=True)
    datos = "Para sacar un turno podés hacerlo online a través de nuestro sistema de turnos."
    if talleres.exists():
        nombres = ', '.join([t.get_nombre() for t in talleres])
        datos += f" Tenemos atención en: {nombres}."

    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
        acciones=[{'texto': 'Sacar turno ahora', 'url': '/turnero/paso1/'}],
    )


def resolver_cancelar_turno(texto, intent, confidence):
    """Cancelación de turno: envía email con link de cancelación (seguridad)"""
    from turnero.models import Turno
    from django.utils import timezone

    # Buscar código de turno en el mensaje
    codigo_match = re.search(r'TRN-[A-Fa-f0-9]{6}', texto.upper())
    if codigo_match:
        codigo = codigo_match.group()
        try:
            turno = Turno.objects.select_related(
                'taller', 'vehiculo', 'cliente', 'tipo_vehiculo'
            ).get(codigo=codigo)
            hoy = timezone.now().date()

            if turno.fecha < hoy:
                datos = (
                    f"El turno {turno.codigo} era para el {turno.fecha.strftime('%d/%m/%Y')} "
                    f"y ya pasó la fecha, por lo que no es necesario cancelarlo."
                )
                return ResolverResult(
                    intent=intent, datos=datos, source='db',
                    necesita_humanizar=True, confidence=1.0,
                    acciones=[{'texto': '📅 Sacar nuevo turno', 'url': '/turnero/paso1/'}],
                )

            if turno.puede_cancelar:
                # Generar token y enviar email con link de cancelación
                try:
                    token = turno.generar_token_cancelacion()
                    from turnero.views_cancelacion import enviar_email_solicitud_cancelacion
                    exito = enviar_email_solicitud_cancelacion(turno, token)
                except Exception:
                    exito = False

                if exito:
                    email_display = turno.cliente.email if turno.cliente else 'tu email registrado'
                    datos = (
                        f"Te enviamos un email a {email_display} con un enlace "
                        f"para cancelar tu turno {turno.codigo}.\n\n"
                        "Por seguridad, la cancelación se confirma desde ese enlace.\n"
                        "El enlace es válido por 48 horas."
                    )
                    return ResolverResult(
                        intent=intent, datos=datos, source='db',
                        necesita_humanizar=True, confidence=1.0,
                    )
                else:
                    datos = (
                        f"Tu turno {turno.codigo} puede ser cancelado, pero hubo un "
                        "problema al enviar el email.\n\n"
                        "Podés cancelarlo desde nuestra web:\n"
                        "1. Ingresá a 'Consultar turno'\n"
                        "2. Buscá tu turno y hacé clic en 'Cancelar'"
                    )
                    return ResolverResult(
                        intent=intent, datos=datos, source='db',
                        necesita_humanizar=True, confidence=1.0,
                        acciones=[{'texto': '📋 Consultar mi turno', 'url': '/turnero/consultar/'}],
                    )
            else:
                if turno.estado in ('COMPLETADO', 'CANCELADO', 'EN_CURSO', 'NO_ASISTIO'):
                    datos = (
                        f"El turno {turno.codigo} no puede cancelarse "
                        f"porque está en estado: {turno.get_estado_display()}."
                    )
                else:
                    datos = (
                        f"El turno {turno.codigo} no puede cancelarse en este momento."
                    )
                return ResolverResult(
                    intent=intent, datos=datos, source='db',
                    necesita_humanizar=True, confidence=1.0,
                )

        except Turno.DoesNotExist:
            return ResolverResult(
                intent=intent,
                datos=f'No se encontró un turno con el código {codigo}.',
                source='db', necesita_humanizar=True, confidence=confidence,
            )

    # Sin código → pedir TRN o patente
    datos = (
        "Para cancelar un turno necesito tu código de turno (formato: TRN-A1B2C3) "
        "o la patente del vehículo.\n\n"
        "Podés escribirlo acá y te ayudo con la cancelación.\n"
        "Si no lo tenés, revisá el email de confirmación que te enviamos al sacar el turno."
    )
    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
        acciones=[
            {'texto': '📋 Consultar en la web', 'url': '/turnero/consultar/'},
        ],
    )


def resolver_reprogramar_turno(texto, intent, confidence):
    """Reprogramación de turno: dispara email con enlace directamente"""
    from turnero.models import Turno
    from django.utils import timezone

    # Buscar código de turno en el mensaje
    codigo_match = re.search(r'TRN-[A-Fa-f0-9]{6}', texto.upper())
    if codigo_match:
        codigo = codigo_match.group()
        try:
            turno = Turno.objects.select_related(
                'taller', 'vehiculo', 'cliente', 'tipo_vehiculo'
            ).get(codigo=codigo)
            hoy = timezone.now().date()

            if turno.fecha < hoy:
                datos = (
                    f"El turno {turno.codigo} era para el {turno.fecha.strftime('%d/%m/%Y')} "
                    f"y ya pasó la fecha, por lo que no se puede reprogramar. "
                    f"Podés sacar un turno nuevo."
                )
                return ResolverResult(
                    intent=intent, datos=datos, source='db',
                    necesita_humanizar=True, confidence=1.0,
                    acciones=[{'texto': '📅 Sacar nuevo turno', 'url': '/turnero/paso1/'}],
                )

            if turno.puede_reprogramar:
                # Disparar email de reprogramación directamente
                try:
                    token = turno.generar_token_reprogramacion()
                    from turnero.views_cancelacion import enviar_email_reprogramacion
                    exito = enviar_email_reprogramacion(turno, token)
                except Exception:
                    exito = False

                if exito:
                    email_display = turno.cliente.email if turno.cliente else 'tu email registrado'
                    datos = (
                        f"¡Listo! Te enviamos un email a {email_display} con un enlace "
                        f"para reprogramar tu turno {turno.codigo}.\n\n"
                        "Desde ese enlace vas a poder elegir la nueva fecha y horario disponible.\n"
                        "El enlace es válido por 48 horas."
                    )
                    return ResolverResult(
                        intent=intent, datos=datos, source='db',
                        necesita_humanizar=True, confidence=1.0,
                    )
                else:
                    datos = (
                        f"Tu turno {turno.codigo} puede ser reprogramado, pero hubo un "
                        "problema al enviar el email.\n\n"
                        "Podés reprogramarlo desde nuestra web:\n"
                        "1. Ingresá a 'Consultar turno'\n"
                        "2. Buscá tu turno y hacé clic en 'Reprogramar'"
                    )
                    return ResolverResult(
                        intent=intent, datos=datos, source='db',
                        necesita_humanizar=True, confidence=1.0,
                        acciones=[{'texto': '📋 Consultar mi turno', 'url': '/turnero/consultar/'}],
                    )
            else:
                if turno.estado in ('COMPLETADO', 'CANCELADO', 'EN_CURSO', 'NO_ASISTIO'):
                    datos = (
                        f"El turno {turno.codigo} no puede reprogramarse "
                        f"porque está en estado: {turno.get_estado_display()}."
                    )
                else:
                    datos = (
                        f"El turno {turno.codigo} no puede reprogramarse en este momento "
                        f"(se requiere al menos 24 horas de anticipación)."
                    )
                return ResolverResult(
                    intent=intent, datos=datos, source='db',
                    necesita_humanizar=True, confidence=1.0,
                    acciones=[{'texto': '📅 Sacar nuevo turno', 'url': '/turnero/paso1/'}],
                )

        except Turno.DoesNotExist:
            return ResolverResult(
                intent=intent,
                datos=f'No se encontró un turno con el código {codigo}.',
                source='db', necesita_humanizar=True, confidence=confidence,
            )

    # Sin código de turno → pedir TRN o patente
    datos = (
        "Para reprogramar un turno necesito tu código de turno (formato: TRN-A1B2C3) "
        "o la patente del vehículo.\n\n"
        "Podés escribirlo acá y te ayudo con la reprogramación.\n"
        "Si no lo tenés, revisá el email de confirmación que te enviamos al sacar el turno."
    )
    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
        acciones=[
            {'texto': '📋 Consultar en la web', 'url': '/turnero/consultar/'},
        ],
    )


def resolver_ubicacion(texto, intent, confidence):
    """Resuelve ubicación de talleres"""
    from talleres.models import Taller

    talleres = Taller.objects.filter(status=True)
    if not talleres.exists():
        return ResolverResult(
            intent=intent, datos='No hay talleres registrados actualmente.',
            source='db', necesita_humanizar=True, confidence=confidence,
        )

    datos_ubicacion = []
    for taller in talleres:
        info = f"- {taller.get_nombre()}"
        if taller.get_direccion():
            info += f": {taller.get_direccion()}"
        if taller.get_localidad():
            info += f", {taller.get_localidad()}"
        if taller.get_telefono():
            info += f" | Tel: {taller.get_telefono()}"
        datos_ubicacion.append(info)

    datos = "Nuestros talleres/plantas:\n" + "\n".join(datos_ubicacion)

    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
        acciones=[{'texto': 'Ver en el mapa', 'scroll_to': '#ubicacion'}],
    )


def resolver_horarios(texto, intent, confidence):
    """Resuelve horarios de atención"""
    from talleres.models import Taller

    talleres = Taller.objects.filter(status=True)
    if not talleres.exists():
        return ResolverResult(
            intent=intent, datos='No hay información de horarios disponible.',
            source='db', necesita_humanizar=True, confidence=confidence,
        )

    datos_horarios = []
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dias_display = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    for taller in talleres:
        horario = f"- {taller.get_nombre()}: {taller.horario_apertura.strftime('%H:%M')} a {taller.horario_cierre.strftime('%H:%M')}"

        # Días de atención
        dias = taller.dias_atencion or {}
        dias_activos = [dias_display[i] for i, d in enumerate(dias_semana) if dias.get(d, False)]
        if dias_activos:
            horario += f" ({', '.join(dias_activos)})"

        datos_horarios.append(horario)

    datos = "Horarios de atención:\n" + "\n".join(datos_horarios)

    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
    )


def resolver_servicios(texto, intent, confidence):
    """Resuelve información de servicios"""
    from core.models import Service

    servicios = Service.objects.filter(active=True).order_by('order')
    if not servicios.exists():
        datos = (
            "Somos una empresa de Revisión Técnica Vehicular (RTV/RTO). "
            "Realizamos inspecciones técnicas obligatorias para todos los tipos de vehículos."
        )
    else:
        datos_servicios = []
        for svc in servicios:
            datos_servicios.append(f"- {svc.title}: {svc.description[:100]}")
        datos = "Nuestros servicios:\n" + "\n".join(datos_servicios)

    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
        acciones=[{'texto': 'Ver servicios', 'scroll_to': '#services'}],
    )


def resolver_disponibilidad(texto, intent, confidence):
    """Resuelve disponibilidad de turnos"""
    from talleres.models import Taller

    talleres = Taller.objects.filter(status=True)
    if talleres.exists():
        datos = (
            "Podés consultar la disponibilidad de turnos directamente en nuestro sistema de turnos online. "
            "Ahí vas a poder elegir el taller, tipo de trámite y ver las fechas y horarios disponibles."
        )
    else:
        datos = "Actualmente no hay talleres configurados para turnos."

    return ResolverResult(
        intent=intent, datos=datos, source='db',
        necesita_humanizar=True, confidence=confidence,
        acciones=[{'texto': 'Ver disponibilidad', 'url': '/turnero/paso1/'}],
    )


def resolver_hablar_con_operador(texto, intent, confidence):
    """Inicia flujo de derivación a operador humano"""
    from talleres.models import Taller
    from .escalation import procesar_derivacion_inicial

    talleres = list(Taller.objects.filter(status=True))
    if not talleres:
        return ResolverResult(
            intent=intent,
            datos='Actualmente no hay talleres configurados para atención.',
            source='db', necesita_humanizar=True, confidence=confidence,
        )

    # Si hay un solo taller, ir directo al paso de verificación de horario
    if len(talleres) == 1:
        return procesar_derivacion_inicial(talleres[0], intent, confidence)

    # Si hay varios, pedir que elija
    acciones = []
    for taller in talleres:
        acciones.append({
            'texto': taller.get_nombre(),
            'accion': f'seleccionar_planta_{taller.pk}',
        })

    return ResolverResult(
        intent=intent,
        respuesta_fija='👤 ¡Por supuesto! ¿Con cuál de nuestras plantas querés comunicarte?',
        source='hardcoded',
        confidence=confidence,
        acciones=acciones,
    )


# Mapa de handlers
HANDLERS = {
    'resolver_tarifas': resolver_tarifas,
    'resolver_consulta_turno': resolver_consulta_turno,
    'resolver_crear_turno': resolver_crear_turno,
    'resolver_cancelar_turno': resolver_cancelar_turno,
    'resolver_reprogramar_turno': resolver_reprogramar_turno,
    'resolver_ubicacion': resolver_ubicacion,
    'resolver_horarios': resolver_horarios,
    'resolver_servicios': resolver_servicios,
    'resolver_disponibilidad': resolver_disponibilidad,
    'resolver_hablar_con_operador': resolver_hablar_con_operador,
}
