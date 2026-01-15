from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Turno, HistorialTurno


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'get_dominio',
        'get_cliente',
        'taller',
        'fecha',
        'hora_inicio',
        'estado_badge',
        'created_at'
    )
    list_filter = (
        'estado',
        'fecha',
        'taller',
        'tipo_vehiculo',
        'created_at'
    )
    search_fields = (
        'codigo',
        'vehiculo__dominio',
        'cliente__nombre',
        'cliente__apellido',
        'cliente__dni',
        'taller__nombre'
    )
    ordering = ('-fecha', '-hora_inicio')
    readonly_fields = (
        'codigo',
        'token_cancelacion',
        'qr_code_display',
        'created_at',
        'updated_at',
        'dias_restantes',
        'puede_cancelar_display'
    )

    autocomplete_fields = ['vehiculo', 'cliente', 'taller', 'tipo_vehiculo']

    fieldsets = (
        ('Información del Turno', {
            'fields': ('codigo', 'vehiculo', 'cliente', 'taller', 'tipo_vehiculo')
        }),
        ('Fecha y Horario', {
            'fields': ('fecha', 'hora_inicio', 'hora_fin')
        }),
        ('Estado', {
            'fields': ('estado', 'observaciones')
        }),
        ('Notificaciones', {
            'fields': (
                'email_enviado',
                'whatsapp_enviado',
                'recordatorio_enviado'
            ),
            'classes': ('collapse',)
        }),
        ('QR Code y Token', {
            'fields': ('qr_code_display', 'token_cancelacion'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'dias_restantes',
                'puede_cancelar_display'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_dominio(self, obj):
        return obj.vehiculo.dominio
    get_dominio.short_description = 'Dominio'
    get_dominio.admin_order_field = 'vehiculo__dominio'

    def get_cliente(self, obj):
        return f"{obj.cliente.apellido}, {obj.cliente.nombre}"
    get_cliente.short_description = 'Cliente'
    get_cliente.admin_order_field = 'cliente__apellido'

    def estado_badge(self, obj):
        colors = {
            'PENDIENTE': '#6c757d',
            'CONFIRMADO': '#0d6efd',
            'EN_CURSO': '#ffc107',
            'COMPLETADO': '#198754',
            'CANCELADO': '#dc3545',
            'NO_ASISTIO': '#fd7e14',
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'

    def qr_code_display(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" width="200" height="200" />')
        return "QR no generado"
    qr_code_display.short_description = 'Código QR'

    def dias_restantes(self, obj):
        dias = obj.dias_para_turno
        if dias < 0:
            return f"Pasó hace {abs(dias)} días"
        elif dias == 0:
            return "HOY"
        else:
            return f"{dias} días"
    dias_restantes.short_description = 'Días para el turno'

    def puede_cancelar_display(self, obj):
        if obj.puede_cancelar:
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 'green', '✓ SÍ')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 'red', '✗ NO')
    puede_cancelar_display.short_description = '¿Puede cancelar?'

    actions = ['marcar_confirmado', 'marcar_en_curso', 'marcar_completado', 'marcar_cancelado']

    def marcar_confirmado(self, request, queryset):
        updated = queryset.update(estado='CONFIRMADO')
        self.message_user(request, f'{updated} turno(s) marcado(s) como CONFIRMADO.')
    marcar_confirmado.short_description = "Marcar como CONFIRMADO"

    def marcar_en_curso(self, request, queryset):
        updated = queryset.update(estado='EN_CURSO')
        self.message_user(request, f'{updated} turno(s) marcado(s) como EN CURSO.')
    marcar_en_curso.short_description = "Marcar como EN CURSO"

    def marcar_completado(self, request, queryset):
        updated = queryset.update(estado='COMPLETADO')
        self.message_user(request, f'{updated} turno(s) marcado(s) como COMPLETADO.')
    marcar_completado.short_description = "Marcar como COMPLETADO"

    def marcar_cancelado(self, request, queryset):
        updated = queryset.update(estado='CANCELADO')
        self.message_user(request, f'{updated} turno(s) marcado(s) como CANCELADO.')
    marcar_cancelado.short_description = "Marcar como CANCELADO"


@admin.register(HistorialTurno)
class HistorialTurnoAdmin(admin.ModelAdmin):
    list_display = (
        'turno',
        'accion',
        'fecha',
        'usuario',
        'ip_address'
    )
    list_filter = ('accion', 'fecha', 'usuario')
    search_fields = (
        'turno__codigo',
        'accion',
        'descripcion',
        'usuario__username'
    )
    ordering = ('-fecha',)
    readonly_fields = ('turno', 'accion', 'descripcion', 'fecha', 'usuario', 'ip_address')

    def has_add_permission(self, request):
        # El historial no se crea manualmente
        return False

    def has_delete_permission(self, request, obj=None):
        # El historial no se elimina
        return False
