from django.contrib import admin
from .models import AsistenteConfigModel, FAQ, ChatSession, ChatMessage, CachedResponse, AIUsageLog


@admin.register(AsistenteConfigModel)
class AsistenteConfigAdmin(admin.ModelAdmin):
    list_display = ['nombre_asistente', 'ai_provider', 'habilitado', 'updated_at']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['pregunta', 'categoria', 'origen', 'veces_usada', 'aprobada', 'status']
    list_filter = ['categoria', 'origen', 'aprobada', 'status']
    search_fields = ['pregunta', 'respuesta_datos']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'ip_address', 'inicio', 'ai_calls_count', 'activa']
    list_filter = ['activa']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'rol', 'intent', 'source', 'created_at']
    list_filter = ['rol', 'source']


@admin.register(CachedResponse)
class CachedResponseAdmin(admin.ModelAdmin):
    list_display = ['pregunta_normalizada', 'intent', 'veces_usada', 'vigente']
    list_filter = ['vigente', 'intent']


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model', 'tokens_input', 'tokens_output', 'exitoso', 'created_at']
    list_filter = ['exitoso', 'provider']
