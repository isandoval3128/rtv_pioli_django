"""
Vistas del panel de administración para el Asistente Virtual IA.
Patrón: @login_required → context → render / JsonResponse
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import timedelta

from collections import Counter

from asistente.models import (
    AsistenteConfigModel, FAQ, ChatSession, ChatMessage,
    CachedResponse, AIUsageLog, SugerenciaAsistente, Derivacion,
    DocumentoKB,
)


# ============================================
# CONFIGURACIÓN DEL ASISTENTE
# ============================================

@login_required(login_url='/panel/login/')
def asistente_config(request):
    from talleres.models import Taller
    context = {
        'titulo': 'Configuración del Asistente IA',
        'config': AsistenteConfigModel.get_config(),
        'talleres': Taller.objects.filter(status=True),
    }
    return render(request, 'panel/asistente_config.html', context)


@login_required(login_url='/panel/login/')
def asistente_config_guardar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    try:
        config = AsistenteConfigModel.get_config()
        config.nombre_asistente = request.POST.get('nombre_asistente', config.nombre_asistente)
        config.system_prompt = request.POST.get('system_prompt', config.system_prompt)
        config.ai_provider = request.POST.get('ai_provider', config.ai_provider)
        config.ai_api_key = request.POST.get('ai_api_key', config.ai_api_key)
        config.ai_model = request.POST.get('ai_model', config.ai_model)
        config.max_tokens_per_request = int(request.POST.get('max_tokens_per_request', config.max_tokens_per_request))
        config.timeout_seconds = int(request.POST.get('timeout_seconds', config.timeout_seconds))
        config.max_ai_calls_per_session = int(request.POST.get('max_ai_calls_per_session', config.max_ai_calls_per_session))
        config.max_ai_calls_per_day = int(request.POST.get('max_ai_calls_per_day', config.max_ai_calls_per_day))
        config.mensaje_bienvenida = request.POST.get('mensaje_bienvenida', config.mensaje_bienvenida)
        config.mensaje_fuera_dominio = request.POST.get('mensaje_fuera_dominio', config.mensaje_fuera_dominio)
        config.mensaje_error = request.POST.get('mensaje_error', config.mensaje_error)
        config.email_resumen_semanal = request.POST.get('email_resumen_semanal', '') or ''
        config.auto_open_delay = int(request.POST.get('auto_open_delay', config.auto_open_delay))
        config.habilitado = request.POST.get('habilitado') == 'on'
        config.save()
        return JsonResponse({'success': True, 'message': 'Configuración guardada correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='/panel/login/')
def asistente_config_test(request):
    """Prueba la conexión con el proveedor de IA"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    from asistente.services.ai_provider import test_connection
    config = AsistenteConfigModel.get_config()
    exitoso, mensaje = test_connection(config)
    return JsonResponse({'success': exitoso, 'message': mensaje})


# ============================================
# GESTIÓN DE FAQs
# ============================================

@login_required(login_url='/panel/login/')
def asistente_faqs(request):
    context = {
        'titulo': 'Preguntas Frecuentes - Asistente IA',
        'categorias': FAQ.CATEGORIA_CHOICES,
    }
    return render(request, 'panel/asistente_faqs.html', context)


@login_required(login_url='/panel/login/')
def asistente_faqs_ajax(request):
    if request.method != 'POST':
        return JsonResponse([], safe=False)

    filtro_categoria = request.POST.get('filtro_categoria', '')
    filtro_origen = request.POST.get('filtro_origen', '')
    filtro_aprobada = request.POST.get('filtro_aprobada', '')

    faqs = FAQ.objects.filter(status=True)

    if filtro_categoria:
        faqs = faqs.filter(categoria=filtro_categoria)
    if filtro_origen:
        faqs = faqs.filter(origen=filtro_origen)
    if filtro_aprobada:
        faqs = faqs.filter(aprobada=filtro_aprobada == 'true')

    data = []
    for faq in faqs.order_by('orden', '-veces_usada'):
        data.append({
            'id': faq.pk,
            'pregunta': faq.pregunta,
            'categoria': faq.get_categoria_display(),
            'categoria_key': faq.categoria,
            'origen': faq.get_origen_display(),
            'origen_key': faq.origen,
            'veces_usada': faq.veces_usada,
            'aprobada': faq.aprobada,
            'orden': faq.orden,
            'created_at': faq.created_at.strftime('%d/%m/%Y %H:%M'),
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/panel/login/')
def asistente_faqs_form(request):
    pk = request.GET.get('pk')
    faq = None
    if pk:
        try:
            faq = FAQ.objects.get(pk=pk)
        except FAQ.DoesNotExist:
            pass

    context = {
        'faq': faq,
        'categorias': FAQ.CATEGORIA_CHOICES,
    }
    html = render_to_string('panel/asistente_faqs_form.html', context, request=request)
    return JsonResponse({'html_form': html})


@login_required(login_url='/panel/login/')
def asistente_faqs_guardar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    try:
        pk = request.POST.get('pk')
        if pk:
            faq = FAQ.objects.get(pk=pk)
        else:
            faq = FAQ()

        faq.pregunta = request.POST.get('pregunta', '')
        faq.respuesta_datos = request.POST.get('respuesta_datos', '')
        faq.categoria = request.POST.get('categoria', 'general')
        faq.orden = int(request.POST.get('orden', 0))

        # Palabras clave: separadas por coma
        palabras_raw = request.POST.get('palabras_clave', '')
        faq.palabras_clave = [p.strip() for p in palabras_raw.split(',') if p.strip()]

        if not pk:
            faq.origen = 'manual'
            faq.aprobada = True

        faq.save()
        return JsonResponse({'success': True, 'message': 'FAQ guardada correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='/panel/login/')
def asistente_faqs_eliminar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pk = request.POST.get('pk')
    try:
        faq = FAQ.objects.get(pk=pk)
        faq.status = False
        faq.save()
        return JsonResponse({'success': True, 'message': 'FAQ eliminada correctamente'})
    except FAQ.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'FAQ no encontrada'})


@login_required(login_url='/panel/login/')
def asistente_faqs_aprobar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pk = request.POST.get('pk')
    try:
        faq = FAQ.objects.get(pk=pk)
        faq.aprobada = True
        faq.save()
        return JsonResponse({'success': True, 'message': 'FAQ aprobada correctamente'})
    except FAQ.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'FAQ no encontrada'})


# ============================================
# CONVERSACIONES
# ============================================

@login_required(login_url='/panel/login/')
def asistente_conversaciones(request):
    # Cerrar sesiones expiradas (más de 24 horas)
    limite = timezone.now() - timedelta(hours=ChatSession.SESSION_DURATION_HOURS)
    expiradas = ChatSession.objects.filter(activa=True, inicio__lt=limite).update(activa=False)

    context = {
        'titulo': 'Conversaciones - Asistente IA',
    }
    return render(request, 'panel/asistente_conversaciones.html', context)


@login_required(login_url='/panel/login/')
def asistente_conversaciones_ajax(request):
    if request.method != 'POST':
        return JsonResponse([], safe=False)

    filtro_fecha_desde = request.POST.get('filtro_fecha_desde', '')
    filtro_fecha_hasta = request.POST.get('filtro_fecha_hasta', '')

    sessions = ChatSession.objects.annotate(
        mensajes_count=Count('mensajes'),
        derivaciones_count=Count('derivaciones'),
    ).order_by('-inicio')

    if filtro_fecha_desde:
        sessions = sessions.filter(inicio__date__gte=filtro_fecha_desde)
    if filtro_fecha_hasta:
        sessions = sessions.filter(inicio__date__lte=filtro_fecha_hasta)

    # Pre-cargar derivaciones para evitar N+1
    sessions_list = list(sessions[:200])
    session_ids = [s.pk for s in sessions_list]
    derivaciones_map = {}
    for d in Derivacion.objects.filter(session_id__in=session_ids).select_related('taller'):
        derivaciones_map[d.session_id] = {
            'canal': d.get_canal_display(),
            'canal_key': d.canal,
            'taller': d.taller.get_nombre() if d.taller else '-',
            'en_horario': d.en_horario,
        }

    data = []
    for s in sessions_list:
        duracion = s.ultima_actividad - s.inicio
        minutos = int(duracion.total_seconds() / 60)
        deriv = derivaciones_map.get(s.pk)
        data.append({
            'id': s.pk,
            'session_key': s.session_key[:12] + '...',
            'ip_address': s.ip_address or '-',
            'inicio': s.inicio.strftime('%d/%m/%Y %H:%M'),
            'mensajes_count': s.mensajes_count,
            'ai_calls': s.ai_calls_count,
            'duracion': f'{minutos} min',
            'activa': s.activa,
            'derivacion': deriv,
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/panel/login/')
def asistente_conversaciones_ver(request):
    pk = request.GET.get('pk')
    try:
        session = ChatSession.objects.get(pk=pk)
        mensajes = ChatMessage.objects.filter(session=session).order_by('created_at')
        derivaciones = Derivacion.objects.filter(session=session).select_related('taller')
    except ChatSession.DoesNotExist:
        return JsonResponse({'html_form': '<p>Sesión no encontrada</p>'})

    context = {
        'session': session,
        'mensajes': mensajes,
        'derivaciones': derivaciones,
    }
    html = render_to_string('panel/asistente_conversaciones_ver.html', context, request=request)
    return JsonResponse({'html_form': html})


# ============================================
# USO IA / COSTOS
# ============================================

@login_required(login_url='/panel/login/')
def asistente_uso_ia(request):
    hoy = timezone.localdate()

    # Estadísticas del día
    logs_hoy = AIUsageLog.objects.filter(created_at__date=hoy)
    stats_hoy = logs_hoy.aggregate(
        total_calls=Count('id'),
        total_tokens_in=Sum('tokens_input'),
        total_tokens_out=Sum('tokens_output'),
        costo_total=Sum('costo_estimado'),
        latencia_avg=Avg('latencia_ms'),
    )

    # Cache hit rate (aproximado)
    mensajes_hoy = ChatMessage.objects.filter(created_at__date=hoy, rol='assistant')
    total_respuestas = mensajes_hoy.count()
    respuestas_cache = mensajes_hoy.filter(source__in=['cache', 'faq', 'hardcoded']).count()
    cache_hit_rate = round((respuestas_cache / total_respuestas * 100) if total_respuestas > 0 else 0, 1)

    context = {
        'titulo': 'Uso IA / Costos - Asistente',
        'total_calls': stats_hoy['total_calls'] or 0,
        'total_tokens': (stats_hoy['total_tokens_in'] or 0) + (stats_hoy['total_tokens_out'] or 0),
        'costo_total': stats_hoy['costo_total'] or 0,
        'latencia_avg': round(stats_hoy['latencia_avg'] or 0),
        'cache_hit_rate': cache_hit_rate,
    }
    return render(request, 'panel/asistente_uso_ia.html', context)


@login_required(login_url='/panel/login/')
def asistente_uso_ia_ajax(request):
    if request.method != 'POST':
        return JsonResponse([], safe=False)

    filtro_fecha_desde = request.POST.get('filtro_fecha_desde', '')
    filtro_fecha_hasta = request.POST.get('filtro_fecha_hasta', '')
    filtro_exitoso = request.POST.get('filtro_exitoso', '')

    logs = AIUsageLog.objects.all().order_by('-created_at')

    if filtro_fecha_desde:
        logs = logs.filter(created_at__date__gte=filtro_fecha_desde)
    if filtro_fecha_hasta:
        logs = logs.filter(created_at__date__lte=filtro_fecha_hasta)
    if filtro_exitoso:
        logs = logs.filter(exitoso=filtro_exitoso == 'true')

    data = []
    for log in logs[:500]:
        data.append({
            'id': log.pk,
            'fecha': log.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'provider': log.provider,
            'model': log.model,
            'tokens_input': log.tokens_input,
            'tokens_output': log.tokens_output,
            'costo': f'${log.costo_estimado:.6f}',
            'latencia': f'{log.latencia_ms}ms',
            'exitoso': log.exitoso,
            'error': log.error_mensaje[:80] if log.error_mensaje else '',
        })

    return JsonResponse(data, safe=False)


# ============================================
# FAQs POR DEFECTO
# ============================================

def _generar_faqs_default():
    """
    Genera FAQs por defecto basadas en los datos reales del sistema.
    Lee la BD y construye preguntas/respuestas contextuales.
    """
    from talleres.models import Taller, TipoVehiculo
    from core.models import SiteConfiguration, Service, WhatsAppConfig

    faqs = []

    # --- TARIFAS ---
    tipos = TipoVehiculo.objects.filter(status=True).order_by('nombre')
    if tipos.exists():
        lineas = []
        for tipo in tipos:
            precios = []
            if tipo.precio_provincial:
                precios.append(f"Provincial: ${tipo.precio_provincial:,.0f}")
            if tipo.precio_nacional:
                precios.append(f"Nacional: ${tipo.precio_nacional:,.0f}")
            if tipo.precio_cajutad:
                precios.append(f"CAJUTAC: ${tipo.precio_cajutad:,.0f}")
            precio_str = ' | '.join(precios) if precios else 'Consultar'
            lineas.append(f"- {tipo.nombre}: {precio_str}")

        faqs.append({
            'pregunta': '¿Cuánto cuesta la revisión técnica vehicular?',
            'palabras_clave': ['tarifa', 'precio', 'costo', 'cuanto sale', 'cuanto cuesta', 'valor'],
            'respuesta_datos': "Las tarifas vigentes son:\n" + "\n".join(lineas),
            'categoria': 'tarifas',
            'orden': 1,
        })

        auto_tipo = tipos.filter(nombre__icontains='auto').first()
        if auto_tipo:
            precios_auto = []
            if auto_tipo.precio_provincial:
                precios_auto.append(f"Provincial: ${auto_tipo.precio_provincial:,.0f}")
            if auto_tipo.precio_nacional:
                precios_auto.append(f"Nacional: ${auto_tipo.precio_nacional:,.0f}")
            faqs.append({
                'pregunta': '¿Cuánto sale la revisión técnica para autos?',
                'palabras_clave': ['auto', 'coche', 'sedan', 'precio auto'],
                'respuesta_datos': f"La revisión técnica para {auto_tipo.nombre} tiene los siguientes precios: {', '.join(precios_auto)}.",
                'categoria': 'tarifas',
                'orden': 2,
            })

    # --- UBICACIÓN ---
    talleres = Taller.objects.filter(status=True)
    if talleres.exists():
        lineas_ubi = []
        for taller in talleres:
            info = f"- {taller.get_nombre()}"
            if taller.get_direccion():
                info += f": {taller.get_direccion()}"
            if taller.get_localidad():
                info += f", {taller.get_localidad()}"
            if taller.get_telefono():
                info += f" | Tel: {taller.get_telefono()}"
            if taller.get_email():
                info += f" | Email: {taller.get_email()}"
            lineas_ubi.append(info)

        faqs.append({
            'pregunta': '¿Dónde queda la planta de revisión técnica?',
            'palabras_clave': ['donde', 'ubicacion', 'direccion', 'planta', 'como llego', 'mapa'],
            'respuesta_datos': "Nuestras plantas de revisión:\n" + "\n".join(lineas_ubi),
            'categoria': 'ubicacion',
            'orden': 3,
        })

    # --- HORARIOS ---
    if talleres.exists():
        dias_display = {
            'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles',
            'jueves': 'Jueves', 'viernes': 'Viernes', 'sabado': 'Sábado', 'domingo': 'Domingo'
        }
        lineas_hor = []
        for taller in talleres:
            hor = f"- {taller.get_nombre()}: {taller.horario_apertura.strftime('%H:%M')} a {taller.horario_cierre.strftime('%H:%M')}"
            dias = taller.dias_atencion or {}
            dias_activos = [dias_display[d] for d in dias_display if dias.get(d, False)]
            if dias_activos:
                hor += f" ({', '.join(dias_activos)})"
            lineas_hor.append(hor)

        faqs.append({
            'pregunta': '¿Cuál es el horario de atención?',
            'palabras_clave': ['horario', 'hora', 'atienden', 'abren', 'cierran', 'dias'],
            'respuesta_datos': "Horarios de atención:\n" + "\n".join(lineas_hor),
            'categoria': 'horarios',
            'orden': 4,
        })

    # --- TURNOS ---
    faqs.append({
        'pregunta': '¿Cómo saco turno para la revisión técnica?',
        'palabras_clave': ['sacar turno', 'pedir turno', 'reservar', 'agendar', 'como saco'],
        'respuesta_datos': "Podés sacar turno de forma online a través de nuestro sistema de turnos en la web. "
                          "Seleccionás el taller, tipo de trámite, elegís fecha y horario disponible, "
                          "y completás tus datos. Recibirás la confirmación por email.",
        'categoria': 'turnos',
        'orden': 5,
    })

    faqs.append({
        'pregunta': '¿Puedo cancelar o reprogramar mi turno?',
        'palabras_clave': ['cancelar', 'reprogramar', 'cambiar turno', 'mover turno', 'anular'],
        'respuesta_datos': "Sí, podés cancelar o reprogramar tu turno. "
                          "En el email de confirmación encontrarás un enlace para cancelar. "
                          "Para reprogramar, podés hacerlo hasta 24 horas antes de la fecha del turno.",
        'categoria': 'turnos',
        'orden': 6,
    })

    faqs.append({
        'pregunta': '¿Cómo consulto el estado de mi turno?',
        'palabras_clave': ['estado turno', 'consultar turno', 'mi turno', 'codigo turno'],
        'respuesta_datos': "Podés consultar el estado de tu turno proporcionando el código de turno "
                          "(formato TRN-XXXXXX) que recibiste por email, o la patente del vehículo.",
        'categoria': 'turnos',
        'orden': 7,
    })

    # --- DOCUMENTACIÓN / REQUISITOS ---
    faqs.append({
        'pregunta': '¿Qué documentación necesito llevar a la revisión técnica?',
        'palabras_clave': ['documentacion', 'documentos', 'requisitos', 'que llevo', 'que necesito', 'papeles'],
        'respuesta_datos': "Para realizar la revisión técnica vehicular necesitás presentar: "
                          "DNI del titular, cédula verde o azul del vehículo, comprobante de seguro vigente, "
                          "y comprobante de pago de patentes al día. "
                          "El vehículo debe estar en condiciones mecánicas básicas (luces, frenos, limpiaparabrisas funcionando).",
        'categoria': 'general',
        'orden': 8,
    })

    faqs.append({
        'pregunta': '¿Cuánto dura la revisión técnica?',
        'palabras_clave': ['cuanto dura', 'tiempo', 'demora', 'duracion', 'cuanto tarda'],
        'respuesta_datos': "La revisión técnica vehicular tiene una duración aproximada de 20 a 40 minutos, "
                          "dependiendo del tipo de vehículo y trámite. "
                          "Te recomendamos llegar unos minutos antes del horario del turno.",
        'categoria': 'general',
        'orden': 9,
    })

    faqs.append({
        'pregunta': '¿Qué pasa si mi vehículo no aprueba la revisión?',
        'palabras_clave': ['no aprueba', 'rechazado', 'reprobado', 'no paso', 'fallo', 'condicional'],
        'respuesta_datos': "Si tu vehículo no aprueba la revisión, recibirás un informe detallado "
                          "con las observaciones y defectos encontrados. Tenés un plazo de 60 días "
                          "para realizar las reparaciones necesarias y volver para una re-inspección "
                          "sin costo adicional (solo se cobra la tasa de re-inspección si corresponde).",
        'categoria': 'general',
        'orden': 10,
    })

    # --- SERVICIOS ---
    servicios = Service.objects.filter(active=True).order_by('order')
    if servicios.exists():
        lineas_svc = [f"- {svc.title}: {svc.description[:150]}" for svc in servicios]
        faqs.append({
            'pregunta': '¿Qué servicios ofrecen?',
            'palabras_clave': ['servicios', 'que ofrecen', 'que hacen', 'tramites disponibles'],
            'respuesta_datos': "Nuestros servicios:\n" + "\n".join(lineas_svc),
            'categoria': 'servicios',
            'orden': 11,
        })

    # --- CONTACTO ---
    try:
        site_config = SiteConfiguration.get_config()
        contacto_info = []
        if site_config.contact_phone:
            contacto_info.append(f"Teléfono: {site_config.contact_phone}")
        if site_config.contact_email:
            contacto_info.append(f"Email: {site_config.contact_email}")
        if site_config.contact_address:
            contacto_info.append(f"Dirección: {site_config.contact_address}")

        try:
            wa = WhatsAppConfig.objects.first()
            if wa and wa.numero_internacional:
                contacto_info.append(f"WhatsApp: {wa.numero_internacional}")
        except Exception:
            pass

        if contacto_info:
            faqs.append({
                'pregunta': '¿Cómo me puedo comunicar con ustedes?',
                'palabras_clave': ['contacto', 'telefono', 'email', 'whatsapp', 'comunicar', 'llamar'],
                'respuesta_datos': "Podés contactarnos por:\n" + "\n".join(f"- {c}" for c in contacto_info),
                'categoria': 'general',
                'orden': 12,
            })
    except Exception:
        pass

    # --- MEDIOS DE PAGO ---
    faqs.append({
        'pregunta': '¿Qué medios de pago aceptan?',
        'palabras_clave': ['pago', 'pagar', 'efectivo', 'tarjeta', 'transferencia', 'medios de pago'],
        'respuesta_datos': "Aceptamos los siguientes medios de pago: efectivo, tarjeta de débito, "
                          "tarjeta de crédito y transferencia bancaria. "
                          "Consultá en la planta por promociones vigentes.",
        'categoria': 'general',
        'orden': 13,
    })

    return faqs


@login_required(login_url='/panel/login/')
def asistente_faqs_default(request):
    """Crea FAQs por defecto basadas en datos del sistema"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    try:
        faqs_default = _generar_faqs_default()
        creadas = 0
        existentes = 0

        for faq_data in faqs_default:
            if FAQ.objects.filter(pregunta__iexact=faq_data['pregunta'], status=True).exists():
                existentes += 1
                continue

            FAQ.objects.create(
                pregunta=faq_data['pregunta'],
                palabras_clave=faq_data['palabras_clave'],
                respuesta_datos=faq_data['respuesta_datos'],
                categoria=faq_data['categoria'],
                orden=faq_data['orden'],
                origen='manual',
                aprobada=True,
            )
            creadas += 1

        msg = f'Se crearon {creadas} FAQs por defecto.'
        if existentes > 0:
            msg += f' ({existentes} ya existían y se omitieron)'

        return JsonResponse({'success': True, 'message': msg, 'creadas': creadas})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ============================================
# SUGERENCIAS DEL ASISTENTE
# ============================================

@login_required(login_url='/panel/login/')
def asistente_sugerencias(request):
    context = {
        'titulo': 'Sugerencias - Asistente IA',
        'categorias': SugerenciaAsistente.CATEGORIA_CHOICES,
        'estados': SugerenciaAsistente.ESTADO_CHOICES,
        'faq_categorias': FAQ.CATEGORIA_CHOICES,
    }
    return render(request, 'panel/asistente_sugerencias.html', context)


@login_required(login_url='/panel/login/')
def asistente_sugerencias_ajax(request):
    if request.method != 'POST':
        return JsonResponse([], safe=False)

    filtro_estado = request.POST.get('filtro_estado', '')
    filtro_categoria = request.POST.get('filtro_categoria', '')

    sugerencias = SugerenciaAsistente.objects.all()

    if filtro_estado:
        sugerencias = sugerencias.filter(estado=filtro_estado)
    if filtro_categoria:
        sugerencias = sugerencias.filter(categoria=filtro_categoria)

    data = []
    for s in sugerencias.order_by('-veces_detectada', '-updated_at')[:200]:
        data.append({
            'id': s.pk,
            'tema': s.tema,
            'categoria': s.get_categoria_display(),
            'categoria_key': s.categoria,
            'estado': s.get_estado_display(),
            'estado_key': s.estado,
            'veces_detectada': s.veces_detectada,
            'ultimo_ejemplo': s.ultimo_ejemplo[:100] + ('...' if len(s.ultimo_ejemplo) > 100 else ''),
            'notas_admin': s.notas_admin[:80] if s.notas_admin else '',
            'session_id': s.session_ejemplo_id,
            'created_at': s.created_at.strftime('%d/%m/%Y'),
            'updated_at': s.updated_at.strftime('%d/%m/%Y'),
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/panel/login/')
def asistente_sugerencias_actualizar(request):
    """Actualiza estado, categoría o notas de una sugerencia"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pk = request.POST.get('pk')
    try:
        sug = SugerenciaAsistente.objects.get(pk=pk)
        campo = request.POST.get('campo')
        valor = request.POST.get('valor', '')

        if campo == 'estado':
            sug.estado = valor
        elif campo == 'categoria':
            sug.categoria = valor
        elif campo == 'notas_admin':
            sug.notas_admin = valor
        else:
            return JsonResponse({'success': False, 'message': 'Campo no válido'})

        sug.save()

        response = {'success': True, 'message': 'Actualizado correctamente'}

        # Si se marcó como revisada, enviar email al gerente con opciones tokenizadas
        if campo == 'estado' and valor == 'revisada':
            from asistente.services.escalation import enviar_email_sugerencia_revision
            email_ok, email_msg = enviar_email_sugerencia_revision(sug)
            response['email_enviado'] = email_ok
            response['email_mensaje'] = email_msg

        # Si se marcó como implementada, ofrecer crear FAQ
        if campo == 'estado' and valor == 'implementada':
            response['crear_faq'] = True
            response['sugerencia'] = {
                'id': sug.pk,
                'tema': sug.tema,
                'ejemplo': sug.ultimo_ejemplo,
            }

        return JsonResponse(response)
    except SugerenciaAsistente.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sugerencia no encontrada'})


@login_required(login_url='/panel/login/')
def asistente_sugerencias_crear_faq(request):
    """Crea una FAQ a partir de una sugerencia marcada como implementada"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pregunta = request.POST.get('pregunta', '').strip()
    respuesta = request.POST.get('respuesta', '').strip()
    categoria = request.POST.get('categoria', 'general')

    if not pregunta or not respuesta:
        return JsonResponse({'success': False, 'message': 'Pregunta y respuesta son obligatorias'})

    try:
        faq = FAQ.objects.create(
            pregunta=pregunta[:500],
            respuesta_datos=respuesta,
            categoria=categoria if categoria in dict(FAQ.CATEGORIA_CHOICES) else 'general',
            origen='manual',
            aprobada=True,
        )
        return JsonResponse({'success': True, 'message': f'FAQ creada correctamente (#{faq.pk})'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al crear FAQ: {e}'})


@login_required(login_url='/panel/login/')
def asistente_sugerencias_eliminar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pk = request.POST.get('pk')
    try:
        sug = SugerenciaAsistente.objects.get(pk=pk)
        sug.delete()
        return JsonResponse({'success': True, 'message': 'Sugerencia eliminada'})
    except SugerenciaAsistente.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sugerencia no encontrada'})


# ============================================
# BASE DE CONOCIMIENTO (KB)
# ============================================

@login_required(login_url='/panel/login/')
def asistente_kb(request):
    context = {
        'titulo': 'Base de Conocimiento - Asistente IA',
        'categorias': DocumentoKB.CATEGORIAS,
    }
    return render(request, 'panel/asistente_kb.html', context)


@login_required(login_url='/panel/login/')
def asistente_kb_ajax(request):
    if request.method != 'POST':
        return JsonResponse([], safe=False)

    filtro_categoria = request.POST.get('filtro_categoria', '')
    filtro_activo = request.POST.get('filtro_activo', '')
    pk = request.POST.get('pk', '')

    docs = DocumentoKB.objects.all()

    if pk:
        docs = docs.filter(pk=pk)
    if filtro_categoria:
        docs = docs.filter(categoria=filtro_categoria)
    if filtro_activo:
        docs = docs.filter(activo=filtro_activo == 'true')

    data = []
    for doc in docs.order_by('-updated_at'):
        keywords = doc.palabras_clave or []
        data.append({
            'id': doc.pk,
            'titulo': doc.titulo,
            'descripcion': doc.descripcion[:100] if doc.descripcion else '',
            'categoria': doc.get_categoria_display(),
            'categoria_key': doc.categoria,
            'palabras_clave': keywords,
            'keywords_preview': keywords[:10],
            'veces_usado': doc.veces_usado,
            'activo': doc.activo,
            'tiene_archivo': bool(doc.archivo),
            'archivo_nombre': doc.archivo.name.split('/')[-1] if doc.archivo else '',
            'contenido_texto': doc.contenido_texto if pk else '',
            'created_at': doc.created_at.strftime('%d/%m/%Y'),
            'updated_at': doc.updated_at.strftime('%d/%m/%Y'),
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/panel/login/')
def asistente_kb_guardar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    try:
        pk = request.POST.get('pk')
        if pk:
            doc = DocumentoKB.objects.get(pk=pk)
        else:
            doc = DocumentoKB()

        doc.titulo = request.POST.get('titulo', '').strip()
        if not doc.titulo:
            return JsonResponse({'success': False, 'message': 'El título es obligatorio'})

        doc.descripcion = request.POST.get('descripcion', '').strip()
        doc.categoria = request.POST.get('categoria', 'general')

        # Contenido de texto manual
        contenido = request.POST.get('contenido_texto', '').strip()
        if contenido:
            doc.contenido_texto = contenido

        # Palabras clave manuales
        keywords_raw = request.POST.get('palabras_clave', '').strip()
        if keywords_raw:
            doc.palabras_clave = [k.strip() for k in keywords_raw.split(',') if k.strip()]

        # Archivo
        archivo = request.FILES.get('archivo')
        if archivo:
            doc.archivo = archivo

        doc.save()

        # Si hay archivo nuevo, procesar (extraer texto + generar keywords)
        if archivo:
            from asistente.services.kb_service import procesar_documento
            procesar_documento(doc)
        elif contenido and not keywords_raw:
            # Si solo se escribió contenido manual sin keywords, generar keywords
            from asistente.services.kb_service import generar_palabras_clave
            doc.palabras_clave = generar_palabras_clave(doc.contenido_texto)
            doc.save(update_fields=['palabras_clave'])

        return JsonResponse({'success': True, 'message': 'Documento guardado correctamente'})
    except DocumentoKB.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Documento no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='/panel/login/')
def asistente_kb_eliminar(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pk = request.POST.get('pk')
    try:
        doc = DocumentoKB.objects.get(pk=pk)
        if doc.archivo:
            doc.archivo.delete(save=False)
        doc.delete()
        return JsonResponse({'success': True, 'message': 'Documento eliminado'})
    except DocumentoKB.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Documento no encontrado'})


@login_required(login_url='/panel/login/')
def asistente_kb_toggle(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    pk = request.POST.get('pk')
    try:
        doc = DocumentoKB.objects.get(pk=pk)
        doc.activo = not doc.activo
        doc.save(update_fields=['activo'])
        estado = 'activado' if doc.activo else 'desactivado'
        return JsonResponse({'success': True, 'message': f'Documento {estado}'})
    except DocumentoKB.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Documento no encontrado'})


# ============================================
# DASHBOARD / ESTADÍSTICAS
# ============================================

@login_required(login_url='/panel/login/')
def asistente_dashboard(request):
    context = {
        'titulo': 'Dashboard - Asistente IA',
    }
    return render(request, 'panel/asistente_dashboard.html', context)


@login_required(login_url='/panel/login/')
def asistente_dashboard_ajax(request):
    """Retorna datos para los gráficos del dashboard"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)

    from datetime import datetime

    periodo = request.POST.get('periodo', 'mes')
    fecha_desde_str = request.POST.get('fecha_desde', '')
    fecha_hasta_str = request.POST.get('fecha_hasta', '')

    hoy = timezone.localdate()

    if periodo == 'hoy':
        fecha_desde = hoy
        fecha_hasta = hoy
    elif periodo == 'semana':
        fecha_desde = hoy - timedelta(days=7)
        fecha_hasta = hoy
    elif periodo == 'mes':
        fecha_desde = hoy - timedelta(days=30)
        fecha_hasta = hoy
    elif periodo == 'custom' and fecha_desde_str and fecha_hasta_str:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
    else:
        fecha_desde = hoy - timedelta(days=30)
        fecha_hasta = hoy

    # === CARDS RESUMEN ===
    sessions = ChatSession.objects.filter(inicio__date__gte=fecha_desde, inicio__date__lte=fecha_hasta)
    mensajes = ChatMessage.objects.filter(created_at__date__gte=fecha_desde, created_at__date__lte=fecha_hasta)
    derivaciones = Derivacion.objects.filter(created_at__date__gte=fecha_desde, created_at__date__lte=fecha_hasta)
    logs_ia = AIUsageLog.objects.filter(created_at__date__gte=fecha_desde, created_at__date__lte=fecha_hasta)

    total_conversaciones = sessions.count()
    total_mensajes = mensajes.count()
    total_derivaciones = derivaciones.count()

    # Tasa resolución (sin operador)
    msgs_asistente = mensajes.filter(rol='assistant')
    total_respuestas = msgs_asistente.count()
    respuestas_resueltas = msgs_asistente.exclude(source='hardcoded').exclude(intent='hablar_con_operador').count()
    tasa_resolucion = round((respuestas_resueltas / total_respuestas * 100) if total_respuestas > 0 else 0, 1)

    # Cache hit rate
    respuestas_cache = msgs_asistente.filter(source__in=['cache', 'faq']).count()
    cache_hit_rate = round((respuestas_cache / total_respuestas * 100) if total_respuestas > 0 else 0, 1)

    # Llamadas IA y costo
    ia_stats = logs_ia.aggregate(
        total_calls=Count('id'),
        costo_total=Sum('costo_estimado'),
    )

    # Documentos KB activos
    docs_kb_activos = DocumentoKB.objects.filter(activo=True).count()

    cards = {
        'total_conversaciones': total_conversaciones,
        'total_mensajes': total_mensajes,
        'tasa_resolucion': tasa_resolucion,
        'total_derivaciones': total_derivaciones,
        'cache_hit_rate': cache_hit_rate,
        'llamadas_ia': ia_stats['total_calls'] or 0,
        'costo_ia': float(ia_stats['costo_total'] or 0),
        'docs_kb_activos': docs_kb_activos,
    }

    # === GRÁFICO: Conversaciones por día ===
    dias_range = (fecha_hasta - fecha_desde).days + 1
    conv_por_dia = {}
    for i in range(min(dias_range, 90)):
        dia = fecha_desde + timedelta(days=i)
        conv_por_dia[dia.strftime('%d/%m')] = 0

    for s in sessions.values('inicio__date').annotate(c=Count('id')):
        label = s['inicio__date'].strftime('%d/%m')
        if label in conv_por_dia:
            conv_por_dia[label] = s['c']

    chart_conv_dia = {
        'labels': list(conv_por_dia.keys()),
        'data': list(conv_por_dia.values()),
    }

    # === GRÁFICO: Intents más consultados ===
    intent_counts = Counter()
    for msg in msgs_asistente.exclude(intent__isnull=True).exclude(intent='').values_list('intent', flat=True):
        intent_counts[msg] += 1

    top_intents = intent_counts.most_common(10)
    chart_intents = {
        'labels': [i[0] for i in top_intents],
        'data': [i[1] for i in top_intents],
    }

    # === GRÁFICO: Source de respuestas (torta) ===
    source_counts = Counter()
    for src in msgs_asistente.exclude(source__isnull=True).values_list('source', flat=True):
        source_counts[src] += 1

    chart_sources = {
        'labels': list(source_counts.keys()),
        'data': list(source_counts.values()),
    }

    # === GRÁFICO: Derivaciones por canal ===
    deriv_canal = Counter()
    for d in derivaciones.values_list('canal', flat=True):
        deriv_canal[d] += 1

    chart_derivaciones_canal = {
        'labels': [{'whatsapp': 'WhatsApp', 'email': 'Email'}.get(k, k) for k in deriv_canal.keys()],
        'data': list(deriv_canal.values()),
    }

    # === GRÁFICO: Horarios pico ===
    hora_counts = Counter()
    for msg in mensajes.filter(rol='user').values_list('created_at', flat=True):
        hora_counts[msg.hour] += 1

    chart_horarios = {
        'labels': [f'{h:02d}:00' for h in range(24)],
        'data': [hora_counts.get(h, 0) for h in range(24)],
    }

    # === TOP SUGERENCIAS ===
    top_sugerencias = list(
        SugerenciaAsistente.objects.filter(estado__in=['nueva', 'revisada'])
        .order_by('-veces_detectada')[:10]
        .values('tema', 'veces_detectada', 'estado')
    )

    return JsonResponse({
        'cards': cards,
        'chart_conv_dia': chart_conv_dia,
        'chart_intents': chart_intents,
        'chart_sources': chart_sources,
        'chart_derivaciones_canal': chart_derivaciones_canal,
        'chart_horarios': chart_horarios,
        'top_sugerencias': top_sugerencias,
    })


@login_required(login_url='/panel/login/')
def asistente_enviar_resumen(request):
    """Envía manualmente el resumen semanal de sugerencias"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

    from asistente.services.escalation import enviar_resumen_semanal
    exitoso, mensaje = enviar_resumen_semanal()
    return JsonResponse({'success': exitoso, 'message': mensaje})
