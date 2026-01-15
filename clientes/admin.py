from django.contrib import admin
from django.utils.html import format_html
from .models import Persona, Cliente


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('dni', 'apellido', 'nombre', 'celular', 'email', 'localidad', 'status')
    list_filter = ('status', 'localidad__departamento')
    search_fields = ('dni', 'nombre', 'apellido', 'email', 'celular')
    autocomplete_fields = ['localidad']
    ordering = ('apellido', 'nombre')

    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'apellido', 'dni', 'cuit', 'fecha_nacimiento')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'celular')
        }),
        ('Ubicación', {
            'fields': ('localidad', 'domicilio')
        }),
        ('Control', {
            'fields': ('status',)
        }),
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'dni',
        'apellido',
        'nombre',
        'estado_badge',
        'tiene_turnos_pendientes',
        'cantidad_turnos_realizados',
        'documentacion_badge',
        'cliente_activo'
    )
    list_filter = (
        'estado_cliente',
        'documentacion_completa',
        'cliente_activo',
        'tiene_turnos_pendientes',
        'localidad__departamento'
    )
    search_fields = ('dni', 'nombre', 'apellido', 'email', 'celular')
    autocomplete_fields = ['localidad']
    ordering = ('apellido', 'nombre')

    readonly_fields = (
        'fecha_registro_cliente',
        'ultima_actualizacion',
        'cantidad_turnos_realizados',
        'cantidad_turnos_cancelados'
    )

    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombre', 'apellido', 'dni', 'cuit', 'fecha_nacimiento')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'celular', 'localidad', 'domicilio')
        }),
        ('Estado del Cliente', {
            'fields': ('estado_cliente', 'cliente_activo', 'tiene_turnos_pendientes'),
            'classes': ('wide',)
        }),
        ('Gestión de Turnos', {
            'fields': ('cantidad_turnos_realizados', 'cantidad_turnos_cancelados', 'ultimo_turno_fecha'),
            'classes': ('collapse',)
        }),
        ('Documentación', {
            'fields': ('documentacion_completa', 'documentos_faltantes', 'notas_internas'),
            'classes': ('collapse',)
        }),
        ('Preferencias de Notificación', {
            'fields': ('acepta_whatsapp', 'acepta_email', 'acepta_sms'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('status', 'fecha_registro_cliente', 'ultima_actualizacion'),
            'classes': ('collapse',)
        })
    )

    actions = ['marcar_documentacion_completa', 'activar_clientes', 'desactivar_clientes', 'marcar_activo']

    def estado_badge(self, obj):
        """Badge con color según estado del cliente"""
        colors = {
            'ACTIVO': '#198754',
            'PENDIENTE_DOCUMENTACION': '#ffc107',
            'PENDIENTE_PAGO': '#fd7e14',
            'DOCUMENTACION_INCOMPLETA': '#dc3545',
            'BLOQUEADO': '#dc3545',
            'INACTIVO': '#6c757d',
        }
        color = colors.get(obj.estado_cliente, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_cliente_display()
        )
    estado_badge.short_description = 'Estado'

    def documentacion_badge(self, obj):
        """Badge para estado de documentación"""
        if obj.documentacion_completa:
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 'green', '✓ Completa')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 'red', '✗ Incompleta')
    documentacion_badge.short_description = 'Documentación'

    def marcar_documentacion_completa(self, request, queryset):
        """Marcar documentación como completa"""
        for cliente in queryset:
            cliente.marcar_documentacion_completa()
        self.message_user(request, f'{queryset.count()} cliente(s) marcados con documentación completa.')
    marcar_documentacion_completa.short_description = "Marcar documentación como completa"

    def activar_clientes(self, request, queryset):
        """Activar clientes seleccionados"""
        updated = queryset.update(cliente_activo=True, estado_cliente='ACTIVO')
        self.message_user(request, f'{updated} cliente(s) activado(s).')
    activar_clientes.short_description = "Activar clientes seleccionados"

    def desactivar_clientes(self, request, queryset):
        """Desactivar clientes seleccionados"""
        updated = queryset.update(cliente_activo=False, estado_cliente='INACTIVO')
        self.message_user(request, f'{updated} cliente(s) desactivado(s).')
    desactivar_clientes.short_description = "Desactivar clientes seleccionados"

    def marcar_activo(self, request, queryset):
        """Marcar como activo"""
        updated = queryset.update(estado_cliente='ACTIVO')
        self.message_user(request, f'{updated} cliente(s) marcados como ACTIVO.')
    marcar_activo.short_description = "Marcar como ACTIVO"
