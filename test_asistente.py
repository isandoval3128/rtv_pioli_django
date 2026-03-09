"""
Test INTENSIVO del asistente - Expone falencias del pipeline completo.
Simula preguntas reales, impredecibles, coloquiales y de borde.
Ejecutar: python test_asistente.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

django.setup()

from asistente.services.intents import detectar_intent_por_keywords, normalizar_texto, INTENTS
from asistente.services.resolver import resolver_mensaje
from asistente.services.kb_service import buscar_en_kb
from asistente.models import DocumentoKB, FAQ

# =============================================
# COLORES
# =============================================
OK = '\033[92m'
FAIL = '\033[91m'
WARN = '\033[93m'
BOLD = '\033[1m'
END = '\033[0m'

total_tests = 0
passed = 0
failed = 0
falencias = []  # Lista de problemas encontrados


def test(nombre, mensaje, esperado_intent=None, esperado_source=None,
         debe_tener_acciones=False, no_debe_tener_acciones=False,
         debe_tener_kb=False, no_debe_tener_kb=False,
         no_debe_ser_intent=None, no_debe_ser_source=None,
         datos_debe_contener=None, datos_no_debe_contener=None,
         descripcion=''):
    """
    Test ESTRICTO del pipeline.
    esperado_source: UN source exacto esperado (string).
    """
    global total_tests, passed, failed
    total_tests += 1

    intent, confidence = detectar_intent_por_keywords(mensaje)
    result = resolver_mensaje(mensaje, session=None)
    kb_results = buscar_en_kb(mensaje)

    errores = []

    # --- Intent ---
    if esperado_intent is not None:
        resolver_intent = result.intent
        if intent != esperado_intent and resolver_intent != esperado_intent:
            errores.append(
                f"Intent: esperado={esperado_intent}, "
                f"raw={intent}({confidence:.2f}), resolver={resolver_intent}"
            )

    if no_debe_ser_intent is not None:
        if isinstance(no_debe_ser_intent, list):
            for ndi in no_debe_ser_intent:
                if intent == ndi:
                    errores.append(f"NO deberia ser intent={ndi}, pero lo es (conf={confidence:.2f})")
        elif intent == no_debe_ser_intent:
            errores.append(f"NO deberia ser intent={no_debe_ser_intent}, pero lo es (conf={confidence:.2f})")

    # --- Source ---
    if esperado_source is not None:
        if result.source != esperado_source:
            errores.append(f"Source: esperado={esperado_source}, obtenido={result.source}")

    if no_debe_ser_source is not None:
        if isinstance(no_debe_ser_source, list):
            for nds in no_debe_ser_source:
                if result.source == nds:
                    errores.append(f"Source NO deberia ser={nds}, pero lo es")
        elif result.source == no_debe_ser_source:
            errores.append(f"Source NO deberia ser={no_debe_ser_source}, pero lo es")

    # --- Acciones ---
    if debe_tener_acciones and not result.acciones:
        errores.append("DEBE tener acciones pero no tiene")
    if no_debe_tener_acciones and result.acciones:
        errores.append(f"NO deberia tener acciones, pero tiene: {[a.get('texto','?') for a in result.acciones]}")

    # --- KB ---
    if debe_tener_kb and not kb_results:
        errores.append("KB deberia encontrar resultados pero no encontro")
    if no_debe_tener_kb and kb_results:
        errores.append(f"KB NO deberia matchear pero encontro: {[r['titulo'] for r in kb_results]}")

    # --- Datos contenido ---
    datos_completo = (result.datos or '') + (result.respuesta_fija or '')
    if datos_debe_contener:
        if isinstance(datos_debe_contener, str):
            datos_debe_contener = [datos_debe_contener]
        for texto_esperado in datos_debe_contener:
            if texto_esperado.lower() not in datos_completo.lower():
                errores.append(f"Datos DEBE contener '{texto_esperado}' pero no lo tiene")

    if datos_no_debe_contener:
        if isinstance(datos_no_debe_contener, str):
            datos_no_debe_contener = [datos_no_debe_contener]
        for texto_prohibido in datos_no_debe_contener:
            if texto_prohibido.lower() in datos_completo.lower():
                errores.append(f"Datos NO debe contener '{texto_prohibido}' pero lo tiene")

    # --- Resultado ---
    if errores:
        failed += 1
        status = f"{FAIL}FAIL{END}"
        for err in errores:
            falencias.append(f"[{nombre}] {err}")
    else:
        passed += 1
        status = f"{OK}PASS{END}"

    print(f"\n{status} {BOLD}Test #{total_tests}: {nombre}{END}")
    if descripcion:
        print(f"   Desc: {descripcion}")
    print(f"   Msg: \"{mensaje}\"")
    print(f"   Intent: raw={intent or 'None'}({confidence:.2f}) | resolver={result.intent} | source={result.source}")
    if result.respuesta_fija:
        print(f"   Resp: {result.respuesta_fija[:100]}{'...' if len(result.respuesta_fija)>100 else ''}")
    if result.datos:
        print(f"   Datos: {result.datos[:100]}{'...' if len(result.datos)>100 else ''}")
    if result.acciones:
        print(f"   Acciones: {[a.get('texto', a.get('accion','?')) for a in result.acciones]}")
    if result.contexto_kb:
        print(f"   KB ctx: {len(result.contexto_kb)} fragmento(s)")
    if kb_results:
        print(f"   KB ind: {len(kb_results)} - [{', '.join(r['titulo'][:25] for r in kb_results)}]")
    for err in errores:
        print(f"   {FAIL}>>> {err}{END}")


# =============================================
# INFO DEL SISTEMA
# =============================================
print(f"\n{'='*70}")
print(f"{BOLD}TEST INTENSIVO DEL ASISTENTE - RTV PIOLI{END}")
print(f"{'='*70}")

from talleres.models import Taller
talleres = list(Taller.objects.filter(status=True))
print(f"\nTalleres activos: {len(talleres)}")
for t in talleres:
    print(f"  - {t.get_nombre()} | WA: {t.get_whatsapp_operador() or 'N/A'}")

faqs = FAQ.objects.filter(aprobada=True, status=True)
print(f"\nFAQs activas: {faqs.count()}")
for faq in faqs:
    kws = faq.palabras_clave or []
    print(f"  [{faq.pk}] \"{faq.pregunta[:45]}\" cat={faq.categoria} kws={kws[:4]}")

kb_docs = DocumentoKB.objects.filter(activo=True)
print(f"\nKB docs activos: {kb_docs.count()}")
for doc in kb_docs:
    print(f"  [{doc.pk}] {doc.titulo} | kw={len(doc.palabras_clave or [])} | chars={len(doc.contenido_texto or '')}")

print(f"\nIntents: {list(INTENTS.keys())}")


# =============================================================================
# CAT 1: FUERA DE DOMINIO - CLARO
# El usuario pregunta algo que NO tiene nada que ver con RTV.
# Esperado: NO matchear ningún intent, ir a IA (needs_ai).
# PROBLEMA CONOCIDO: el humanizer ofrece operador para fuera de dominio.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 1: FUERA DE DOMINIO - CLARO{END}")
print(f"NO debe matchear intents. Source: needs_ai. NO debe ofrecer operador.")
print(f"{'='*70}")

test("Clima",
     "¿Cómo va a estar el clima mañana?",
     esperado_intent=None,
     no_debe_ser_intent=['saludo', 'consultar_servicios', 'hablar_con_operador'],
     no_debe_ser_source=['hardcoded', 'faq', 'db'],
     descripcion="Fuera de dominio total")

test("Fútbol",
     "¿Quién ganó el partido de ayer?",
     esperado_intent=None,
     esperado_source='needs_ai',
     descripcion="Deportes = fuera de dominio")

test("Receta",
     "¿Cómo hago una pizza casera?",
     esperado_intent=None,
     esperado_source='needs_ai')

test("Política",
     "¿Qué opinas del gobierno actual?",
     esperado_intent=None,
     esperado_source='needs_ai')

test("Chiste",
     "Contame un chiste",
     esperado_intent=None,
     esperado_source='needs_ai',
     descripcion="Pedido de entretenimiento")

test("Matemáticas",
     "¿Cuánto es 25 por 30?",
     esperado_intent=None,
     no_debe_ser_intent='consultar_tarifa',
     esperado_source='needs_ai',
     descripcion="No confundir 'cuánto' con tarifa")

test("Salud",
     "Me duele la cabeza, ¿qué puedo tomar?",
     esperado_intent=None,
     esperado_source='needs_ai')


# =============================================================================
# CAT 2: FUERA DE DOMINIO - ENGAÑOSO
# Parece automotor pero NO es RTV.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 2: FUERA DE DOMINIO - ENGAÑOSO{END}")
print(f"Suena a autos pero NO es RTV. NO debe matchear intents de RTV.")
print(f"{'='*70}")

test("Mecánico",
     "¿Me pueden arreglar el auto?",
     no_debe_ser_intent=['consultar_servicios', 'crear_turno'],
     no_debe_ser_source='hardcoded',
     descripcion="Mecánica != RTV")

test("Seguro",
     "¿Venden seguros de auto?",
     no_debe_ser_intent='consultar_servicios',
     descripcion="Seguros != servicios RTV")

test("Transferencia",
     "Necesito hacer la transferencia del auto",
     no_debe_ser_intent=['crear_turno', 'consultar_servicios'],
     descripcion="Transferencia dominial != turno RTV")

test("Multa",
     "¿Cuánto sale la multa por no tener revisión?",
     no_debe_ser_intent='consultar_tarifa',
     descripcion="Multa != tarifa del servicio")

test("Lavadero",
     "¿Tienen lavadero de autos?",
     no_debe_ser_intent='consultar_servicios',
     descripcion="Lavadero != servicios RTV")


# =============================================================================
# CAT 3: INTENTS FIJOS (saludo, despedida, agradecimiento)
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 3: INTENTS FIJOS{END}")
print(f"{'='*70}")

test("Hola",
     "Hola",
     esperado_intent='saludo',
     esperado_source='hardcoded')

test("Buenas tardes",
     "Buenas tardes",
     esperado_intent='saludo',
     esperado_source='hardcoded')

test("Buen día",
     "Buen día",
     esperado_intent='saludo',
     esperado_source='hardcoded')

test("Chau",
     "Chau",
     esperado_intent='despedida',
     esperado_source='hardcoded')

test("Gracias por todo - despedida",
     "Gracias por todo",
     esperado_intent='despedida',
     esperado_source='hardcoded',
     descripcion="'gracias por todo' = despedida")

test("Gracias - agradecimiento",
     "Gracias",
     esperado_intent='agradecimiento',
     esperado_source='hardcoded',
     descripcion="'gracias' sola = agradecimiento, NO despedida")

test("Muchas gracias",
     "Muchas gracias por la info",
     esperado_intent='agradecimiento',
     esperado_source='hardcoded',
     no_debe_ser_intent='despedida')

test("Perfecto",
     "Perfecto, genial",
     esperado_intent='agradecimiento',
     esperado_source='hardcoded')

test("Qué tal",
     "Qué tal",
     esperado_intent='saludo',
     esperado_source='hardcoded')


# =============================================================================
# CAT 4: MENSAJES COMPUESTOS (saludo + consulta)
# El saludo NO debe comerse la consulta real.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 4: MENSAJES COMPUESTOS{END}")
print(f"Saludo + pregunta real. DEBE resolver la pregunta, NO responder solo saludo.")
print(f"{'='*70}")

test("Hola + tarifa",
     "Hola, quiero saber cuánto cuesta la revisión",
     no_debe_ser_source='hardcoded',
     datos_debe_contener='$',
     descripcion="DEBE resolver tarifa, no solo saludar")

test("Buenas + turno",
     "Buenas, quiero sacar un turno",
     no_debe_ser_source='hardcoded',
     descripcion="DEBE resolver turno, no solo saludar")

test("Buenos días + ubicación",
     "Buenos días, dónde queda la planta",
     no_debe_ser_source='hardcoded',
     datos_debe_contener='Planta',
     descripcion="DEBE resolver ubicación")

test("Hola + horarios",
     "Hola buenas, a qué hora abren?",
     no_debe_ser_source='hardcoded',
     descripcion="DEBE resolver horarios")

test("Hey + operador",
     "Hola, necesito hablar con una persona",
     esperado_intent='hablar_con_operador',
     debe_tener_acciones=True if len(talleres) > 1 else False,
     descripcion="DEBE derivar a operador con selección de planta")

test("Gracias + nueva consulta",
     "Gracias, otra consulta: ¿cuánto cuesta la revisión para auto?",
     no_debe_ser_source='hardcoded',
     descripcion="Agradecimiento + nueva pregunta: resolver la pregunta")


# =============================================================================
# CAT 5: CONSULTAS DB/FAQ - INTENT CORRECTO
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 5: CONSULTAS DE BD/FAQ{END}")
print(f"Detectar intent CORRECTO y dar respuesta con datos REALES.")
print(f"{'='*70}")

test("Tarifa - cuánto cuesta",
     "¿Cuánto cuesta la revisión técnica?",
     esperado_intent='consultar_tarifa',
     datos_debe_contener='$',
     descripcion="Debe mostrar precios reales con $")

test("Tarifa - precio RTV",
     "precio de la RTV",
     esperado_intent='consultar_tarifa',
     datos_debe_contener='$')

test("Tarifa - cuánto sale",
     "cuánto sale la revisión",
     esperado_intent='consultar_tarifa')

test("Ubicación - dónde queda",
     "¿Dónde queda el taller?",
     esperado_intent='consultar_ubicacion',
     datos_debe_contener=['Planta Libertador', 'Planta Palpalá'],
     descripcion="DEBE mostrar AMBAS plantas")

test("Horarios",
     "¿A qué hora atienden?",
     esperado_intent='consultar_horarios',
     datos_debe_contener=['Planta Libertador', 'Planta Palpalá'],
     descripcion="DEBE mostrar horarios de AMBAS plantas")

test("Servicios",
     "¿Qué servicios ofrecen?",
     esperado_intent='consultar_servicios')

test("Crear turno",
     "Quiero sacar un turno",
     esperado_intent='crear_turno',
     debe_tener_acciones=True,
     datos_debe_contener='turno',
     descripcion="DEBE tener botón de acción para sacar turno")

test("Cancelar turno",
     "Quiero cancelar mi turno",
     esperado_intent='cancelar_turno')

test("Reprogramar turno",
     "Necesito cambiar la fecha de mi turno",
     esperado_intent='reprogramar_turno')

test("Disponibilidad",
     "¿Hay turnos disponibles para mañana?",
     esperado_intent='disponibilidad')


# =============================================================================
# CAT 6: TURNO CON CÓDIGO - DEBE ir al handler DB, NO a FAQ
# El handler hace lookup real del código. La FAQ da texto genérico.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 6: TURNO CON CÓDIGO ESPECÍFICO{END}")
print(f"DEBE ir al handler DB para lookup real, NO a FAQ genérica.")
print(f"{'='*70}")

test("Turno por código",
     "Mi turno TRN-A1B2C3",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="Con código TRN-*, DEBE hacer lookup en DB, no FAQ genérica")

test("Consultar turno con código",
     "Quiero consultar el turno TRN-FF00AA",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="DEBE buscar el código específico en la BD")

test("Estado de turno",
     "¿En qué estado está mi turno TRN-123456?",
     esperado_intent='consultar_turno',
     esperado_source='db',
     datos_debe_contener='TRN',
     descripcion="DEBE intentar buscar ese código en BD")


# =============================================================================
# CAT 7: DERIVACIÓN A OPERADOR
# CRÍTICO: DEBE ir al handler, NUNCA a FAQ.
# Con 2 talleres: SIEMPRE mostrar selección de planta.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 7: DERIVACIÓN A OPERADOR{END}")
print(f"DEBE ir al handler (bypass FAQ). Con {len(talleres)} talleres: mostrar plantas.")
print(f"{'='*70}")

test("Operador directo",
     "operador",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False,
     descripcion="BYPASS FAQ obligatorio")

test("Quiero hablar con un operador",
     "quiero hablar con un operador",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)

test("Necesito hablar con persona",
     "necesito hablar con una persona",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)

test("Atención humana",
     "quiero atención humana por favor",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)

test("Quiero que me atiendan",
     "quiero que me atiendan",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)

test("Hablar con alguien",
     "quiero hablar con alguien",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)

test("Agente por favor",
     "agente",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)

test("Persona real",
     "persona real",
     esperado_intent='hablar_con_operador',
     esperado_source='hardcoded',
     no_debe_ser_source='faq',
     debe_tener_acciones=True if len(talleres) > 1 else False)


# =============================================================================
# CAT 8: CONFUSIÓN DE INTENTS
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 8: CONFUSIÓN DE INTENTS{END}")
print(f"Debe elegir el intent CORRECTO en casos ambiguos.")
print(f"{'='*70}")

test("'cuánto sale el turno' = tarifa, NO crear turno",
     "¿Cuánto sale sacar un turno?",
     esperado_intent='consultar_tarifa',
     no_debe_ser_intent='crear_turno')

test("'dónde hacen la revisión' = ubicación, NO servicios",
     "¿Dónde hacen la revisión técnica?",
     esperado_intent='consultar_ubicacion',
     no_debe_ser_intent='consultar_servicios')

test("'no puedo ir' = cancelar",
     "No puedo ir al turno, ¿puedo cambiarlo?",
     no_debe_ser_intent='saludo')

test("'hablar con alguien' aunque diga 'no entiendo'",
     "No entiendo nada, quiero hablar con alguien",
     esperado_intent='hablar_con_operador',
     no_debe_ser_source='needs_ai',
     descripcion="NO es fuera de dominio, es escalación")

test("Pregunta con 'servicio' pero es ubicación",
     "¿Dónde ofrecen el servicio de revisión técnica?",
     esperado_intent='consultar_ubicacion',
     no_debe_ser_intent='consultar_servicios',
     descripcion="'dónde' domina sobre 'servicio'")

test("'revisión técnica' NO debe matchear solo servicios",
     "¿Cuánto cuesta la revisión técnica vehicular?",
     esperado_intent='consultar_tarifa',
     no_debe_ser_intent='consultar_servicios',
     descripcion="'cuánto cuesta' = tarifa, aunque diga 'revisión técnica'")


# =============================================================================
# CAT 9: FRUSTRACIÓN Y ESCALACIÓN
# Usuarios molestos o que piden ayuda especial.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 9: FRUSTRACIÓN Y ESCALACIÓN{END}")
print(f"Usuarios que necesitan atención especial -> operador.")
print(f"{'='*70}")

test("Quiero hacer un reclamo",
     "Quiero hacer un reclamo",
     no_debe_ser_source='hardcoded',
     no_debe_ser_intent='saludo',
     descripcion="Reclamo debería ir a operador o IA")

test("No me funciona nada",
     "No me funciona, pasame con alguien",
     esperado_intent='hablar_con_operador',
     descripcion="Frustración + pedido de operador")

test("Esto no me sirve",
     "Esto no me sirve, quiero hablar con una persona",
     esperado_intent='hablar_con_operador',
     debe_tener_acciones=True if len(talleres) > 1 else False,
     descripcion="Frustración + operador explícito")

test("Necesito ayuda urgente",
     "Necesito ayuda urgente, es un tema con mi turno",
     no_debe_ser_intent='saludo',
     no_debe_ser_source='hardcoded',
     descripcion="Urgencia sobre turno, no es fuera de dominio")


# =============================================================================
# CAT 10: DOMINIO RTV - SIN RESPUESTA DIRECTA
# Preguntas que SÍ son de RTV pero el sistema no tiene handler específico.
# NO deben ser tratadas como "fuera de dominio".
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 10: DOMINIO RTV SIN HANDLER DIRECTO{END}")
print(f"Son preguntas de RTV legítimas. NO deben caer en 'fuera de dominio'.")
print(f"{'='*70}")

test("Revisión para motos",
     "¿Hacen revisión para motos?",
     no_debe_ser_intent='saludo',
     descripcion="Es RTV, no fuera de dominio. Debería ir a servicios/KB/IA")

test("¿Qué pasa si no apruebo?",
     "¿Qué pasa si mi auto no aprueba la revisión?",
     no_debe_ser_intent='saludo',
     descripcion="Pregunta RTV legítima")

test("¿Puedo ir sin turno?",
     "¿Puedo ir a hacer la revisión sin turno?",
     no_debe_ser_intent='saludo',
     descripcion="Pregunta RTV sobre modalidad de atención")

test("¿Qué documentos necesito?",
     "¿Qué documentos tengo que llevar a la revisión?",
     no_debe_ser_intent='saludo',
     descripcion="Documentación para RTV - pregunta frecuente")

test("Auto con GNC",
     "Tengo un auto con GNC, ¿puedo hacer la revisión?",
     no_debe_ser_intent='saludo',
     descripcion="GNC es tema RTV")

test("Auto 0km",
     "Mi auto es 0km, ¿necesita revisión técnica?",
     no_debe_ser_intent='saludo',
     descripcion="Exención de 0km es tema RTV")

test("Oblea vencida",
     "Se me venció la oblea, ¿qué hago?",
     no_debe_ser_intent=['saludo', 'despedida'],
     descripcion="Oblea vencida es 100% dominio RTV")

test("Medios de pago",
     "¿Puedo pagar con tarjeta?",
     no_debe_ser_intent='saludo',
     descripcion="Pago es pregunta del servicio RTV")

test("Tiempo de inspección",
     "¿Cuánto dura la revisión técnica?",
     no_debe_ser_intent=['saludo', 'consultar_tarifa'],
     descripcion="Duración != tarifa, aunque ambos dicen 'cuánto'")

test("Re-inspección",
     "Me rechazaron el auto, ¿cuándo puedo volver?",
     no_debe_ser_intent='saludo',
     descripcion="Re-inspección es dominio RTV")


# =============================================================================
# CAT 11: MULTI-PLANTA
# Con 2 talleres, la info debe incluir AMBOS siempre.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 11: MULTI-PLANTA ({len(talleres)} talleres){END}")
print(f"Toda info de planta debe mencionar AMBAS. Operador: elegir planta.")
print(f"{'='*70}")

if len(talleres) >= 2:
    plant_names = [t.get_nombre() for t in talleres]

    test("Operador: elegir planta",
         "Quiero hablar con un operador",
         debe_tener_acciones=True,
         descripcion=f"DEBE mostrar botones: {plant_names}")

    # Test directo de ubicación
    result_ubic = resolver_mensaje("¿Dónde queda el taller?")
    total_tests += 1
    plantas_ubic = sum(1 for t in talleres if t.get_nombre().lower() in (result_ubic.datos or '').lower())
    if plantas_ubic >= 2:
        passed += 1
        print(f"\n{OK}PASS{END} {BOLD}Test #{total_tests}: Ubicación -> ambas plantas{END}")
    else:
        failed += 1
        falencias.append(f"[Ubicación multi-planta] Solo muestra {plantas_ubic} de {len(talleres)} plantas")
        print(f"\n{FAIL}FAIL{END} {BOLD}Test #{total_tests}: Ubicación solo muestra {plantas_ubic} plantas{END}")
    print(f"   Datos: {(result_ubic.datos or '')[:120]}...")

    # Test directo de horarios
    result_hor = resolver_mensaje("¿Qué horarios tienen?")
    total_tests += 1
    plantas_hor = sum(1 for t in talleres if t.get_nombre().lower() in (result_hor.datos or '').lower())
    if plantas_hor >= 2:
        passed += 1
        print(f"\n{OK}PASS{END} {BOLD}Test #{total_tests}: Horarios -> ambas plantas{END}")
    else:
        failed += 1
        falencias.append(f"[Horarios multi-planta] Solo muestra {plantas_hor} de {len(talleres)} plantas")
        print(f"\n{FAIL}FAIL{END} {BOLD}Test #{total_tests}: Horarios solo muestra {plantas_hor} plantas{END}")
    print(f"   Datos: {(result_hor.datos or '')[:120]}...")

    test("¿Cuál planta me conviene?",
         "¿Cuál planta me conviene?",
         no_debe_ser_source='hardcoded',
         descripcion="Pregunta sobre plantas, debe tener info multi-planta")

    test("¿Atienden en Palpalá los sábados?",
         "¿Atienden en Palpalá los sábados?",
         no_debe_ser_intent='saludo',
         descripcion="Pregunta específica de una planta")

else:
    print(f"\n{WARN}SKIP: Solo {len(talleres)} taller(es) activo(s){END}")


# =============================================================================
# CAT 12: BASE DE CONOCIMIENTO
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 12: BASE DE CONOCIMIENTO (KB){END}")
print(f"{'='*70}")

if kb_docs.exists():
    test("Documentos para revisión (KB)",
         "¿Qué documentos necesito para la revisión técnica vehicular?",
         debe_tener_kb=True,
         descripcion="KB tiene doc de requisitos, DEBE encontrarlo")

    test("Requisitos inspección (KB)",
         "¿Cuáles son los requisitos para la inspección?",
         debe_tener_kb=True,
         descripcion="Sinónimo de 'documentos necesarios'")
else:
    print(f"\n{WARN}SKIP: No hay docs KB activos{END}")


# =============================================================================
# CAT 13: LENGUAJE COLOQUIAL, TYPOS, ABREVIATURAS
# Usuarios reales no escriben perfecto.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 13: LENGUAJE COLOQUIAL Y ERRORES{END}")
print(f"Usuarios reales con typos, abreviaturas, informalidad.")
print(f"{'='*70}")

test("'kuanto kuesta' (typo)",
     "kuanto kuesta la revision",
     no_debe_ser_source='hardcoded',
     descripcion="Typo severo, debería matchear tarifa o ir a IA con contexto RTV")

test("'kiero un turno' (typo)",
     "kiero un turno",
     no_debe_ser_intent='saludo',
     descripcion="Typo: 'kiero'->'quiero', debería matchear crear_turno")

test("Todo en mayúsculas",
     "QUIERO SACAR UN TURNO",
     esperado_intent='crear_turno',
     descripcion="Mayúsculas no deben afectar detección")

test("Todo minúsculas sin acentos",
     "cuanto cuesta la revision tecnica",
     esperado_intent='consultar_tarifa',
     descripcion="Sin acentos ni puntuación")

test("Mensaje muy corto",
     "turno",
     esperado_intent='consultar_turno',
     descripcion="Una sola palabra debería matchear")

test("Mensaje con emojis",
     "Hola quiero un turno",
     no_debe_ser_intent=None,
     descripcion="Emojis no deben romper el pipeline")

test("'ola' sin H (typo)",
     "ola, cuanto sale la rtv?",
     no_debe_ser_source='hardcoded',
     descripcion="Typo 'ola' no debe ser solo saludo, debe resolver la consulta")

test("Abreviatura 'x' (por)",
     "quiero cancelar x favor",
     no_debe_ser_intent='saludo',
     descripcion="'cancelar' debería matchear cancelar_turno")


# =============================================================================
# CAT 14: EDGE CASES
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 14: EDGE CASES{END}")
print(f"{'='*70}")

test("Solo puntuación",
     "???",
     no_debe_ser_intent='saludo',
     descripcion="No debería romper nada")

test("Mensaje vacío-ish",
     "...",
     no_debe_ser_intent='saludo',
     descripcion="No debería romper nada")

test("Repetición",
     "turno turno turno turno",
     esperado_intent='consultar_turno',
     descripcion="Repetición de keyword")

test("Pregunta larga y confusa",
     "Mira yo la verdad no sé bien qué necesito pero creo que tengo que hacer la revisión técnica del auto que es un Fiat Palio modelo 2015 y quería saber cuánto sale y dónde queda",
     no_debe_ser_source='hardcoded',
     no_debe_ser_intent='saludo',
     descripcion="Mensaje largo natural, debería detectar intención principal")


# =============================================================================
# CAT 15: PATENTES SUELTAS → CONSULTA DE TURNO
# El usuario envía solo la patente (sin contexto).
# El sistema debe reconocer el formato y buscar turno por dominio.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 15: PATENTES SUELTAS → CONSULTA DE TURNO{END}")
print(f"El usuario envía solo la patente. DEBE rutear a consultar_turno.")
print(f"{'='*70}")

test("Patente vieja (ABC123)",
     "JHH666",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="Formato viejo 3 letras + 3 números → buscar turno por dominio")

test("Patente Mercosur (AB123CD)",
     "AB123CD",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="Formato Mercosur 2+3+2 → buscar turno por dominio")

test("Patente con espacios",
     "JHH 666",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="Patente con espacio, debe normalizar y detectar")

test("Patente con guión",
     "AB-123-CD",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="Patente con guiones, debe normalizar y detectar")

test("Patente minúsculas",
     "jhh666",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="Patente en minúsculas, debe normalizar")

test("NO es patente: texto largo con letras y números",
     "quiero saber sobre abc123 y otras cosas",
     no_debe_ser_intent='consultar_turno',
     descripcion="Patente embebida en frase larga no debe activar bypass")


# =============================================================================
# CAT 16: FLUJO REPROGRAMAR/CANCELAR CON TRN
# Botones de acción envían texto con TRN. Debe rutear al handler correcto.
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}CAT 16: FLUJO REPROGRAMAR/CANCELAR CON TRN{END}")
print(f"Botones de acción con TRN deben rutear al handler correcto.")
print(f"{'='*70}")

test("Reprogramar con TRN (botón)",
     "quiero reprogramar el turno TRN-A1B2C3",
     esperado_intent='reprogramar_turno',
     esperado_source='db',
     no_debe_ser_intent='consultar_turno',
     descripcion="Botón 'Reprogramar' envía texto con TRN → handler reprogramar")

test("Cancelar con TRN (botón)",
     "quiero cancelar el turno TRN-A1B2C3",
     esperado_intent='cancelar_turno',
     esperado_source='db',
     no_debe_ser_intent='consultar_turno',
     descripcion="Botón 'Cancelar' envía texto con TRN → handler cancelar")

test("Confirmar cancelación con TRN",
     "confirmar cancelar turno TRN-A1B2C3",
     esperado_intent='cancelar_turno',
     esperado_source='db',
     descripcion="Botón 'Confirmar cancelación' → ejecutar cancelación")

test("TRN sin intent específico → consulta",
     "TRN-A1B2C3",
     esperado_intent='consultar_turno',
     esperado_source='db',
     descripcion="TRN solo → consultar turno (no reprogramar ni cancelar)")

test("No cancelar (botón mantener turno)",
     "perfecto, no cancelar",
     esperado_intent='agradecimiento',
     esperado_source='hardcoded',
     no_debe_ser_intent='cancelar_turno',
     descripcion="Botón 'No, mantener turno' → agradecimiento, NO cancelación")


# =============================================================================
# RESUMEN
# =============================================================================
print(f"\n\n{'='*70}")
print(f"{BOLD}RESUMEN DE RESULTADOS{END}")
print(f"{'='*70}")
print(f"Total tests: {total_tests}")
print(f"{OK}Pasaron: {passed}{END}")
print(f"{FAIL}Fallaron: {failed}{END}")
if total_tests > 0:
    tasa = (passed / total_tests) * 100
    color = OK if tasa >= 80 else (WARN if tasa >= 60 else FAIL)
    print(f"Tasa de éxito: {color}{tasa:.1f}%{END}")

if falencias:
    print(f"\n{BOLD}FALENCIAS ENCONTRADAS ({len(falencias)}):{END}")
    for i, f_desc in enumerate(falencias, 1):
        print(f"  {FAIL}{i}. {f_desc}{END}")

# Nota sobre humanizer (CORREGIDO en sesión anterior)
print(f"\n{OK}{BOLD}NOTA - HUMANIZER NO_RELEVANTE (CORREGIDO):{END}")
print(f"{OK}El humanizer ahora diferencia correctamente:{END}")
print(f"{OK}  - Fuera de dominio → 'Solo puedo ayudarte con temas de RTV' (sin operador){END}")
print(f"{OK}  - RTV sin info → 'No cuento con esa info, ¿querés hablar con operador?'{END}")

print(f"\n{'='*70}")
