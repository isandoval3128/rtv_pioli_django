import uuid
from datetime import timedelta

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class AsistenteConfigModel(models.Model):
    """Configuración del Asistente Virtual (Singleton)"""

    PROVIDER_CHOICES = [
        ('gemini_flash', 'Google Gemini Flash'),
        ('openai', 'OpenAI'),
        ('custom', 'Proveedor personalizado'),
    ]

    # General
    nombre_asistente = models.CharField(
        max_length=100, default='Asistente Virtual',
        verbose_name='Nombre del asistente')
    system_prompt = models.TextField(
        default='Sos un asistente virtual amable y profesional de una empresa de Revisión Técnica Vehicular (RTV). '
                'Respondés en español argentino, de forma clara, cálida y natural. '
                'Ayudás a los usuarios con consultas sobre turnos, tarifas, ubicación y servicios.',
        verbose_name='Prompt del sistema',
        help_text='Personalidad e instrucciones base para la IA')

    # Proveedor IA
    ai_provider = models.CharField(
        max_length=20, choices=PROVIDER_CHOICES, default='gemini_flash',
        verbose_name='Proveedor de IA')
    ai_api_key = models.CharField(
        max_length=255, blank=True,
        verbose_name='API Key',
        help_text='Clave de API del proveedor seleccionado')
    ai_model = models.CharField(
        max_length=100, default='gemini-2.0-flash',
        verbose_name='Modelo de IA',
        help_text='Nombre del modelo a utilizar')
    max_tokens_per_request = models.IntegerField(
        default=300,
        verbose_name='Máx. tokens por solicitud')
    timeout_seconds = models.IntegerField(
        default=10,
        verbose_name='Timeout (segundos)',
        help_text='Tiempo máximo de espera para la respuesta de la IA')

    # Límites de uso
    max_ai_calls_per_session = models.IntegerField(
        default=20,
        verbose_name='Máx. llamadas IA por sesión')
    max_ai_calls_per_day = models.IntegerField(
        default=500,
        verbose_name='Máx. llamadas IA por día')
    umbral_cache_similarity = models.FloatField(
        default=0.85,
        verbose_name='Umbral similitud cache',
        help_text='Valor entre 0 y 1. A mayor valor, más exacta debe ser la coincidencia para usar cache.')

    # Mensajes predeterminados
    mensaje_bienvenida = models.TextField(
        default='¡Hola! Soy el asistente virtual de RTV Pioli. '
                '¿En qué puedo ayudarte? Podés preguntarme sobre turnos, tarifas, ubicación o nuestros servicios.',
        verbose_name='Mensaje de bienvenida')
    mensaje_fuera_dominio = models.TextField(
        default='Disculpá, solo puedo ayudarte con temas relacionados a la Revisión Técnica Vehicular: '
                'turnos, tarifas, ubicación y servicios. ¿Hay algo de eso en lo que pueda asistirte?',
        verbose_name='Mensaje fuera de dominio')
    mensaje_error = models.TextField(
        default='Perdón, tuve un problema procesando tu consulta. '
                'Por favor intentá de nuevo o contactanos por WhatsApp.',
        verbose_name='Mensaje de error')

    # Email resumen semanal
    email_resumen_semanal = models.EmailField(
        blank=True,
        verbose_name='Email para resumen semanal',
        help_text='Recibe un resumen semanal de sugerencias y consultas no resueltas')

    # Widget UX
    auto_open_delay = models.IntegerField(
        default=3000,
        verbose_name='Auto-apertura (ms)',
        help_text='Milisegundos que el chat permanece abierto al cargar la página. 0 = deshabilitado.')

    # Estado
    habilitado = models.BooleanField(
        default=True,
        verbose_name='Asistente habilitado')
    status = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Configuración del Asistente'
        verbose_name_plural = 'Configuración del Asistente'

    def __str__(self):
        return f"Configuración del Asistente - {self.nombre_asistente}"

    def save(self, *args, **kwargs):
        if not self.pk and AsistenteConfigModel.objects.exists():
            raise ValidationError('Solo puede existir una configuración del asistente')
        return super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(pk=1)
        return config


class FAQ(models.Model):
    """Preguntas frecuentes gestionadas manualmente o sugeridas por IA"""

    CATEGORIA_CHOICES = [
        ('turnos', 'Turnos'),
        ('tarifas', 'Tarifas'),
        ('ubicacion', 'Ubicación'),
        ('servicios', 'Servicios'),
        ('horarios', 'Horarios'),
        ('general', 'General'),
    ]

    ORIGEN_CHOICES = [
        ('manual', 'Manual'),
        ('sugerida_ia', 'Sugerida por IA'),
    ]

    pregunta = models.CharField(max_length=500, verbose_name='Pregunta')
    palabras_clave = models.JSONField(
        default=list, blank=True,
        verbose_name='Palabras clave',
        help_text='Lista de palabras clave para matching. Ej: ["tarifa", "precio", "costo"]')
    respuesta_datos = models.TextField(
        verbose_name='Respuesta (datos)',
        help_text='Respuesta con los datos concretos que el asistente usará')
    respuesta_humanizada = models.TextField(
        blank=True,
        verbose_name='Respuesta humanizada (cache)',
        help_text='Versión humanizada por IA (se genera automáticamente)')
    categoria = models.CharField(
        max_length=20, choices=CATEGORIA_CHOICES, default='general',
        verbose_name='Categoría')
    origen = models.CharField(
        max_length=20, choices=ORIGEN_CHOICES, default='manual',
        verbose_name='Origen')
    veces_usada = models.IntegerField(default=0, verbose_name='Veces utilizada')
    aprobada = models.BooleanField(default=True, verbose_name='Aprobada')
    orden = models.IntegerField(default=0, verbose_name='Orden')
    status = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Pregunta Frecuente'
        verbose_name_plural = 'Preguntas Frecuentes'
        ordering = ['orden', '-veces_usada']

    def __str__(self):
        return self.pregunta[:80]


class ChatSession(models.Model):
    """Sesión de chat de un visitante"""

    session_key = models.CharField(
        max_length=100, unique=True,
        verbose_name='Clave de sesión')
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name='Dirección IP')
    inicio = models.DateTimeField(auto_now_add=True, verbose_name='Inicio')
    ultima_actividad = models.DateTimeField(auto_now=True, verbose_name='Última actividad')
    ai_calls_count = models.IntegerField(default=0, verbose_name='Llamadas IA')
    contexto = models.JSONField(
        default=dict, blank=True,
        verbose_name='Contexto de la conversación')
    activa = models.BooleanField(default=True, verbose_name='Activa')

    class Meta:
        verbose_name = 'Sesión de Chat'
        verbose_name_plural = 'Sesiones de Chat'
        ordering = ['-ultima_actividad']

    SESSION_DURATION_HOURS = 24

    def esta_expirada(self):
        """Verifica si la sesión superó las 24 horas desde su inicio"""
        return timezone.now() - self.inicio > timedelta(hours=self.SESSION_DURATION_HOURS)

    def cerrar_si_expirada(self):
        """Cierra la sesión si está expirada. Retorna True si se cerró."""
        if self.activa and self.esta_expirada():
            self.activa = False
            self.save(update_fields=['activa'])
            return True
        return False

    def __str__(self):
        return f"Sesión {self.session_key[:12]}... ({self.inicio.strftime('%d/%m/%Y %H:%M')})"


class ChatMessage(models.Model):
    """Mensaje individual dentro de una sesión de chat"""

    ROL_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
    ]

    SOURCE_CHOICES = [
        ('faq', 'FAQ'),
        ('cache', 'Cache'),
        ('db', 'Base de datos'),
        ('ai', 'Inteligencia Artificial'),
        ('kb+ai', 'Base de Conocimiento + IA'),
        ('hardcoded', 'Respuesta fija'),
    ]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE,
        related_name='mensajes', verbose_name='Sesión')
    rol = models.CharField(
        max_length=10, choices=ROL_CHOICES,
        verbose_name='Rol')
    contenido = models.TextField(verbose_name='Contenido')
    intent = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name='Intención detectada')
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, null=True, blank=True,
        verbose_name='Fuente de la respuesta')
    faq_usada = models.ForeignKey(
        FAQ, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='FAQ utilizada')
    tokens_usados = models.IntegerField(default=0, verbose_name='Tokens usados')
    tiempo_respuesta_ms = models.IntegerField(default=0, verbose_name='Tiempo de respuesta (ms)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Mensaje de Chat'
        verbose_name_plural = 'Mensajes de Chat'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.rol}] {self.contenido[:60]}..."


class CachedResponse(models.Model):
    """Cache de respuestas humanizadas para evitar llamadas repetidas a la IA"""

    pregunta_normalizada = models.CharField(
        max_length=500,
        verbose_name='Pregunta normalizada')
    intent = models.CharField(
        max_length=50,
        verbose_name='Intención')
    datos_contexto = models.JSONField(
        default=dict, blank=True,
        verbose_name='Datos de contexto usados')
    respuesta = models.TextField(verbose_name='Respuesta cacheada')
    veces_usada = models.IntegerField(default=0, verbose_name='Veces utilizada')
    vigente = models.BooleanField(default=True, verbose_name='Vigente')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        verbose_name = 'Respuesta en Cache'
        verbose_name_plural = 'Respuestas en Cache'
        ordering = ['-veces_usada']

    def __str__(self):
        return f"Cache: {self.pregunta_normalizada[:60]}..."


class Derivacion(models.Model):
    """Registro de derivaciones a operador humano"""

    CANAL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
    ]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE,
        related_name='derivaciones', verbose_name='Sesión')
    taller = models.ForeignKey(
        'talleres.Taller', on_delete=models.SET_NULL, null=True,
        verbose_name='Taller')
    canal = models.CharField(
        max_length=10, choices=CANAL_CHOICES,
        verbose_name='Canal de derivación')
    motivo = models.TextField(
        blank=True, verbose_name='Resumen de la conversación')
    celular_cliente = models.CharField(
        max_length=20, blank=True,
        verbose_name='Celular del cliente',
        help_text='Número que dejó el cliente para ser contactado')
    en_horario = models.BooleanField(
        default=True, verbose_name='Dentro del horario de atención')
    email_enviado = models.BooleanField(
        default=False, verbose_name='Email enviado')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Derivación a Operador'
        verbose_name_plural = 'Derivaciones a Operador'
        ordering = ['-created_at']

    def __str__(self):
        return f"Derivación [{self.canal}] - {self.taller} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"


class SugerenciaAsistente(models.Model):
    """Sugerencias detectadas automáticamente de consultas no resueltas"""

    CATEGORIA_CHOICES = [
        ('funcionalidad', 'Funcionalidad'),
        ('informacion', 'Información'),
        ('servicio', 'Servicio'),
        ('otro', 'Otro'),
    ]

    ESTADO_CHOICES = [
        ('nueva', 'Nueva'),
        ('revisada', 'Revisada'),
        ('planificada', 'Planificada'),
        ('implementada', 'Implementada'),
        ('descartada', 'Descartada'),
    ]

    tema = models.CharField(
        max_length=200, verbose_name='Tema')
    tema_normalizado = models.CharField(
        max_length=200, verbose_name='Tema normalizado')
    categoria = models.CharField(
        max_length=20, choices=CATEGORIA_CHOICES, default='otro',
        verbose_name='Categoría')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='nueva',
        verbose_name='Estado')
    veces_detectada = models.IntegerField(
        default=1, verbose_name='Veces detectada')
    ultimo_ejemplo = models.TextField(
        blank=True, verbose_name='Último mensaje ejemplo')
    session_ejemplo = models.ForeignKey(
        ChatSession, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Sesión ejemplo')
    notas_admin = models.TextField(
        blank=True, verbose_name='Notas del administrador')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de detección')
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Sugerencia del Asistente'
        verbose_name_plural = 'Sugerencias del Asistente'
        ordering = ['-veces_detectada', '-updated_at']

    def __str__(self):
        return f"[{self.estado}] {self.tema[:60]} (x{self.veces_detectada})"


class SugerenciaToken(models.Model):
    """Token seguro para acciones sobre sugerencias desde email"""

    ACCION_CHOICES = [
        ('implementar', 'Implementar'),
        ('declinar', 'Declinar'),
    ]

    sugerencia = models.ForeignKey(
        SugerenciaAsistente, on_delete=models.CASCADE,
        related_name='tokens', verbose_name='Sugerencia')
    token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False,
        verbose_name='Token')
    accion = models.CharField(
        max_length=20, choices=ACCION_CHOICES,
        verbose_name='Acción')
    usado = models.BooleanField(
        default=False, verbose_name='Usado')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de creación')
    expires_at = models.DateTimeField(
        verbose_name='Fecha de expiración')

    class Meta:
        verbose_name = 'Token de Sugerencia'
        verbose_name_plural = 'Tokens de Sugerencia'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def esta_vigente(self):
        return not self.usado and timezone.now() < self.expires_at

    def __str__(self):
        return f"Token [{self.accion}] para Sugerencia #{self.sugerencia_id}"


class DocumentoKB(models.Model):
    """Documento de la Base de Conocimiento para el asistente"""

    CATEGORIAS = [
        ('procedimiento', 'Procedimiento'),
        ('normativa', 'Normativa'),
        ('manual', 'Manual'),
        ('informe', 'Informe'),
        ('general', 'General'),
    ]

    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    categoria = models.CharField(
        max_length=20, choices=CATEGORIAS, default='general',
        verbose_name='Categoría')
    archivo = models.FileField(
        upload_to='asistente/kb/', blank=True, null=True,
        verbose_name='Archivo fuente',
        help_text='PDF, Word o texto. Se extrae el contenido automáticamente.')
    contenido_texto = models.TextField(
        blank=True,
        verbose_name='Contenido',
        help_text='Texto del documento. Se llena automáticamente al subir archivo, o manualmente.')
    palabras_clave = models.JSONField(
        default=list, blank=True,
        verbose_name='Palabras clave',
        help_text='Lista de keywords para búsqueda. Se generan automáticamente.')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    veces_usado = models.PositiveIntegerField(default=0, verbose_name='Veces utilizado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Documento KB'
        verbose_name_plural = 'Documentos KB'
        ordering = ['-updated_at']

    def __str__(self):
        return self.titulo


class AIUsageLog(models.Model):
    """Log de uso de la IA para monitoreo y control de costos"""

    session = models.ForeignKey(
        ChatSession, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Sesión')
    provider = models.CharField(max_length=50, verbose_name='Proveedor')
    model = models.CharField(max_length=100, verbose_name='Modelo')
    tokens_input = models.IntegerField(default=0, verbose_name='Tokens entrada')
    tokens_output = models.IntegerField(default=0, verbose_name='Tokens salida')
    costo_estimado = models.DecimalField(
        max_digits=10, decimal_places=6, default=0,
        verbose_name='Costo estimado (USD)')
    latencia_ms = models.IntegerField(default=0, verbose_name='Latencia (ms)')
    exitoso = models.BooleanField(default=True, verbose_name='Exitoso')
    error_mensaje = models.TextField(blank=True, verbose_name='Mensaje de error')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Log de Uso IA'
        verbose_name_plural = 'Logs de Uso IA'
        ordering = ['-created_at']

    def __str__(self):
        status = "OK" if self.exitoso else "ERROR"
        return f"[{status}] {self.provider}/{self.model} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
