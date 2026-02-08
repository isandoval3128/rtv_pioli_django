"""
Definición de intenciones (intents) del asistente virtual.
Cada intent tiene keywords para matching y un handler que resuelve datos.
"""
import re
from difflib import SequenceMatcher

INTENTS = {
    # --- Respuestas fijas (sin IA, sin DB) ---
    'saludo': {
        'keywords': ['hola', 'buenas', 'buen dia', 'buenos dias', 'buenas tardes',
                     'buenas noches', 'que tal', 'hey', 'hi', 'hello'],
        'tipo': 'fijo',
    },
    'despedida': {
        'keywords': ['chau', 'adios', 'hasta luego', 'nos vemos',
                     'bye', 'gracias por todo'],
        'tipo': 'fijo',
    },
    'agradecimiento': {
        'keywords': ['gracias', 'muchas gracias', 'te agradezco', 'genial', 'perfecto',
                     'excelente', 'barbaro', 'buenisimo'],
        'tipo': 'fijo',
    },

    # --- Consultas que requieren datos de DB ---
    'consultar_tarifa': {
        'keywords': ['tarifa', 'precio', 'costo', 'cuanto sale', 'cuanto cuesta',
                     'valor', 'cuanto vale', 'presupuesto', 'cotizacion',
                     'provincial', 'nacional', 'cajutac'],
        'negative_keywords': ['multa', 'infraccion', 'sancion', 'penalidad'],
        'tipo': 'db',
        'handler': 'resolver_tarifas',
    },
    'consultar_turno': {
        'keywords': ['turno', 'mi turno', 'consultar turno', 'estado turno',
                     'buscar turno', 'codigo turno', 'trn-'],
        'tipo': 'db',
        'handler': 'resolver_consulta_turno',
    },
    'crear_turno': {
        'keywords': ['sacar turno', 'pedir turno', 'reservar turno', 'agendar turno',
                     'nuevo turno', 'quiero turno', 'necesito turno', 'hacer turno',
                     'solicitar turno', 'obtener turno'],
        'negative_keywords': ['cambiar', 'reprogramar', 'cancelar', 'anular',
                              'mover', 'consultar', 'estado'],
        'tipo': 'db',
        'handler': 'resolver_crear_turno',
    },
    'cancelar_turno': {
        'keywords': ['cancelar turno', 'cancelar', 'anular turno', 'anular',
                     'dar de baja turno', 'no puedo ir', 'cancelar mi turno',
                     'confirmar cancelar turno', 'confirmar cancelar',
                     'confirmo cancelar turno', 'confirmo cancelar'],
        'tipo': 'db',
        'handler': 'resolver_cancelar_turno',
    },
    'reprogramar_turno': {
        'keywords': ['reprogramar turno', 'reprogramar', 'cambiar turno',
                     'mover turno', 'cambiar fecha', 'cambiar horario',
                     'reagendar', 'reprogramacion'],
        'tipo': 'db',
        'handler': 'resolver_reprogramar_turno',
    },
    'consultar_ubicacion': {
        'keywords': ['ubicacion', 'donde queda', 'donde hacen', 'donde esta',
                     'direccion', 'como llego', 'donde',
                     'mapa', 'planta', 'taller', 'donde estan', 'sucursal',
                     'donde ofrecen', 'donde realizan'],
        'tipo': 'db',
        'handler': 'resolver_ubicacion',
    },
    'consultar_horarios': {
        'keywords': ['horario', 'horarios', 'a que hora', 'que dias',
                     'dias de atencion', 'abren', 'cierran', 'atienden',
                     'hora de apertura', 'hora de cierre'],
        'tipo': 'db',
        'handler': 'resolver_horarios',
    },
    'consultar_servicios': {
        'keywords': ['servicio', 'servicios', 'que hacen', 'que ofrecen',
                     'revision tecnica', 'rtv', 'rto', 'vtv', 'oblea',
                     'inspeccion', 'que tramites'],
        'tipo': 'db',
        'handler': 'resolver_servicios',
    },
    'gestion_post_tramite': {
        'keywords': ['copia de mi rtv', 'copia rtv', 'copia del rtv',
                     'copia de mi rto', 'copia certificado', 'duplicado oblea',
                     'duplicado rtv', 'copia aprobado', 'rtv aprobado',
                     'certificado aprobado', 'constancia aprobado',
                     'resultado de mi revision', 'resultado revision',
                     'me aprobaron', 'me rechazaron'],
        'tipo': 'db',
        'handler': 'resolver_gestion_post_tramite',
    },
    'disponibilidad': {
        'keywords': ['disponibilidad', 'hay turno', 'turnos disponibles',
                     'proximos turnos', 'hay lugar', 'cuando hay turno'],
        'tipo': 'db',
        'handler': 'resolver_disponibilidad',
    },
    'hablar_con_operador': {
        'keywords': ['hablar con operador', 'hablar con persona', 'hablar con humano',
                     'quiero hablar con alguien', 'operador', 'persona real',
                     'atencion humana', 'agente', 'hablar con un agente',
                     'representante', 'atencion personalizada', 'quiero que me atiendan',
                     'hablar con alguien', 'necesito hablar con una persona',
                     'pasame con alguien', 'pasame con una persona', 'pasame con operador',
                     'pasame con un operador'],
        'tipo': 'db',
        'handler': 'resolver_hablar_con_operador',
    },
}

# Respuestas fijas por intent
RESPUESTAS_FIJAS = {
    'saludo': [
        '👋 ¡Hola! ¿En qué puedo ayudarte hoy?',
        '😊 ¡Buenas! Estoy acá para lo que necesites. ¿Qué consulta tenés?',
        '👋 ¡Hola! Bienvenido a RTV Pioli. ¿Cómo puedo ayudarte?',
    ],
    'despedida': [
        '👋 ¡Hasta luego! Cualquier cosa, acá estamos.',
        '😊 ¡Chau! Que tengas un buen día.',
        '🙌 ¡Nos vemos! Si necesitás algo más, no dudes en escribirnos.',
    ],
    'agradecimiento': [
        '😊 ¡De nada! Me alegra poder ayudarte.',
        '🙌 ¡Con gusto! Si tenés otra consulta, acá estoy.',
        '😊 ¡No hay de qué! Para eso estamos.',
    ],
}


def normalizar_texto(texto):
    """Normaliza texto para comparación: minúsculas, sin acentos, sin puntuación"""
    texto = texto.lower().strip()
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n',
    }
    for orig, reempl in reemplazos.items():
        texto = texto.replace(orig, reempl)
    # Eliminar puntuación que interfiere con matching
    texto = re.sub(r'[¿?¡!.,;:()\[\]{}"\'«»—–\-]', ' ', texto)
    # Colapsar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def _palabra_fuzzy_match(palabra, keyword_palabra, umbral=0.75):
    """Compara dos palabras con tolerancia a errores tipográficos.
    Solo aplica fuzzy en palabras de 4+ caracteres (las cortas requieren exacto)."""
    if palabra == keyword_palabra:
        return True
    if len(palabra) < 4 or len(keyword_palabra) < 4:
        return False
    return SequenceMatcher(None, palabra, keyword_palabra).ratio() >= umbral


def _keyword_fuzzy_en_texto(keyword_norm, texto_normalizado, palabras_texto):
    """Verifica si un keyword (puede ser multi-palabra) matchea con fuzzy en el texto.
    Retorna un score: 0 = no match, 0.7 = fuzzy match."""
    kw_words = keyword_norm.split()

    if len(kw_words) == 1:
        # Keyword de una sola palabra: buscar fuzzy contra cada palabra del texto
        for palabra in palabras_texto:
            if _palabra_fuzzy_match(palabra, kw_words[0]):
                return 0.7
    else:
        # Keyword multi-palabra: todas las palabras deben tener fuzzy match
        matched = 0
        for kw in kw_words:
            for palabra in palabras_texto:
                if _palabra_fuzzy_match(palabra, kw):
                    matched += 1
                    break
        if matched == len(kw_words):
            return 0.7

    return 0


def detectar_intent_por_keywords(texto):
    """
    Detecta el intent más probable basado en keywords.
    Usa matching exacto primero, y fuzzy matching como fallback para typos.
    Retorna (intent_name, confidence) o (None, 0)
    """
    texto_normalizado = normalizar_texto(texto)
    palabras_texto = set(texto_normalizado.split())
    mejor_intent = None
    mejor_score = 0

    for intent_name, intent_data in INTENTS.items():
        score = 0
        for keyword in intent_data['keywords']:
            keyword_norm = normalizar_texto(keyword)

            if ' ' in keyword_norm:
                # --- Keyword MULTI-PALABRA ---
                # Match exacto de substring
                if keyword_norm in texto_normalizado:
                    if texto_normalizado == keyword_norm:
                        score += 3
                    elif texto_normalizado.startswith(keyword_norm):
                        score += 2
                    else:
                        score += 1
                else:
                    # Match por palabras individuales
                    kw_words = set(keyword_norm.split())
                    matches = kw_words & palabras_texto
                    if len(matches) == len(kw_words):
                        score += 1.5
                    else:
                        fuzzy_score = _keyword_fuzzy_en_texto(keyword_norm, texto_normalizado, palabras_texto)
                        if fuzzy_score > 0:
                            score += fuzzy_score
            else:
                # --- Keyword UNA SOLA PALABRA ---
                if len(keyword_norm) <= 3:
                    # Keywords cortas (hi, hey, bye, rtv, rto, vtv):
                    # solo word match exacto (evitar 'hi' en 'chiste', 'vehicular')
                    if keyword_norm in palabras_texto:
                        if texto_normalizado == keyword_norm:
                            score += 3
                        elif len(palabras_texto) <= 2:
                            score += 2
                        else:
                            score += 1
                else:
                    # Keywords largas (4+ chars): substring match
                    if keyword_norm in texto_normalizado:
                        if texto_normalizado == keyword_norm:
                            score += 3
                        elif texto_normalizado.startswith(keyword_norm):
                            score += 2
                        else:
                            score += 1
                    else:
                        fuzzy_score = _keyword_fuzzy_en_texto(keyword_norm, texto_normalizado, palabras_texto)
                        if fuzzy_score > 0:
                            score += fuzzy_score

        # Penalizar por negative_keywords (desambiguación)
        # Incluye fuzzy matching para que typos como "cncelar" penalicen igual que "cancelar"
        if score > 0 and 'negative_keywords' in intent_data:
            for neg_kw in intent_data['negative_keywords']:
                neg_norm = normalizar_texto(neg_kw)
                if neg_norm in palabras_texto or neg_norm in texto_normalizado:
                    score = 0
                    break
                # Fuzzy match en negative_keywords (typos)
                if _keyword_fuzzy_en_texto(neg_norm, texto_normalizado, palabras_texto) > 0:
                    score = 0
                    break

        if score > mejor_score:
            mejor_score = score
            mejor_intent = intent_name

    confidence = min(mejor_score / 3.0, 1.0) if mejor_score > 0 else 0
    return mejor_intent, confidence
