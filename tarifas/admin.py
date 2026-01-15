from django.contrib import admin
from .models import Tarifa


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status_display", "created", "updated")
    search_fields = ("titulo", "descripcion")
    list_filter = ("status", "created")
    readonly_fields = ("created", "updated")
    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'archivo_excel')
        }),
        ('Estado', {
            'fields': ('status',),
            'description': 'Solo puede haber una tarifa vigente a la vez. Al marcar esta como vigente, las demás se desmarcarán automáticamente.'
        }),
        ('Auditoría', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        """Muestra un ícono visual para el estado"""
        if obj.status:
            return "✓ VIGENTE"
        return "○ No vigente"
    status_display.short_description = "Estado"

    class Media:
        css = {
            'all': ('admin/css/tarifa_admin.css',)
        }
