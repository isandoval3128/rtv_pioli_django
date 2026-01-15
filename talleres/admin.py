from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from .models import Taller, TipoVehiculo, ConfiguracionTaller, Vehiculo
from .forms import TallerAdminForm
from .utils import importar_tramites_desde_excel


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    form = TallerAdminForm
    list_display = (
        'nombre',
        'planta',
        'get_localidad_display',
        'get_telefono_display',
        'horario_display',
        'status',
        'created_at'
    )
    list_filter = ('status', 'planta', 'localidad__departamento', 'created_at')
    search_fields = ('nombre', 'direccion', 'telefono', 'email', 'planta__nombre')
    ordering = ('nombre',)
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['localidad', 'planta']

    fieldsets = (
        ('Referencia a Planta', {
            'fields': ('planta',),
            'description': 'Si se selecciona una planta, se usarán automáticamente sus datos de ubicación y contacto. Los campos siguientes solo se usarán si NO hay planta seleccionada.'
        }),
        ('Información Básica', {
            'fields': ('nombre',),
        }),
        ('Datos de Ubicación y Contacto (solo si NO hay planta)', {
            'fields': ('direccion', 'localidad', 'telefono', 'email', 'latitud', 'longitud'),
            'classes': ('collapse', 'datos-propios-taller'),
            'description': 'Estos campos solo son necesarios si NO se seleccionó una planta arriba'
        }),
        ('Horarios de Atención', {
            'fields': ('horario_apertura', 'horario_cierre', 'dias_atencion')
        }),
        ('Fechas Especiales', {
            'fields': ('fechas_no_laborables_text',),
            'classes': ('collapse',),
            'description': 'Configurá fechas en las que el taller NO estará disponible (feriados, vacaciones, días de mantenimiento, etc.)'
        }),
        ('Estado', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

    class Media:
        js = ('admin/js/taller_admin.js',)

    def get_localidad_display(self, obj):
        """Muestra la localidad, priorizando la de la planta"""
        localidad = obj.get_localidad()
        return localidad if localidad else '-'
    get_localidad_display.short_description = 'Localidad'
    get_localidad_display.admin_order_field = 'localidad'

    def get_telefono_display(self, obj):
        """Muestra el teléfono, priorizando el de la planta"""
        return obj.get_telefono() or '-'
    get_telefono_display.short_description = 'Teléfono'

    def horario_display(self, obj):
        return f"{obj.horario_apertura.strftime('%H:%M')} - {obj.horario_cierre.strftime('%H:%M')}"
    horario_display.short_description = 'Horario'


class ImportarExcelForm(forms.Form):
    """Formulario para subir archivo Excel manualmente"""
    archivo_excel = forms.FileField(
        label="Archivo Excel",
        help_text="Archivo .xlsx con la estructura: CODIGO | TARIFA | PROVINCIAL | NACIONAL | CAJUTAC"
    )


@admin.register(TipoVehiculo)
class TipoVehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_tramite',
        'nombre',
        'precios_display',
        'duracion_minutos',
        'status',
        'updated'
    )
    list_filter = ('status', 'created')
    search_fields = ('codigo_tramite', 'nombre', 'descripcion')
    ordering = ('codigo_tramite', 'nombre')
    list_editable = ('status',)
    readonly_fields = ('created', 'updated')
    change_list_template = 'admin/talleres/tipovehiculo_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'importar/',
                self.admin_site.admin_view(self.importar_excel_view),
                name='talleres_tipovehiculo_importar'
            ),
        ]
        return custom_urls + urls

    fieldsets = (
        ('Información del Trámite', {
            'fields': ('codigo_tramite', 'nombre', 'descripcion')
        }),
        ('Precios', {
            'fields': ('precio_provincial', 'precio_nacional', 'precio_cajutad'),
            'description': 'Los precios se importan automáticamente desde la Tarifa vigente'
        }),
        ('Configuración', {
            'fields': ('duracion_minutos', 'status')
        }),
        ('Auditoría', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def precios_display(self, obj):
        return obj.get_precio_display()
    precios_display.short_description = 'Precios'

    def importar_excel_view(self, request):
        """
        Vista para importar trámites desde un archivo Excel subido manualmente.
        Accesible desde el botón en la lista de TipoVehiculo.
        """
        import tempfile
        import os

        if request.method == 'POST' and 'apply' in request.POST:
            # Procesar el archivo subido
            form = ImportarExcelForm(request.POST, request.FILES)
            if form.is_valid():
                archivo = request.FILES['archivo_excel']

                # Guardar archivo temporalmente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    for chunk in archivo.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name

                try:
                    # Importar desde el archivo temporal
                    creados, errores, lista_errores = importar_tramites_desde_excel(tmp_path)

                    # Mensaje de éxito
                    if creados > 0:
                        self.message_user(
                            request,
                            f"Se importaron {creados} trámites exitosamente.",
                            messages.SUCCESS
                        )
                    if errores > 0:
                        mensaje_error = f"Se encontraron {errores} errores:\n"
                        for error in lista_errores[:5]:  # Mostrar solo los primeros 5
                            mensaje_error += f"- {error}\n"
                        self.message_user(request, mensaje_error, messages.WARNING)

                finally:
                    # Limpiar archivo temporal
                    os.unlink(tmp_path)

                return redirect('admin:talleres_tipovehiculo_changelist')

        # Mostrar formulario
        form = ImportarExcelForm()
        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar Trámites desde Excel',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/importar_excel.html', context)

    class Media:
        css = {
            'all': ('admin/css/tipo_tramite_admin.css',)
        }


@admin.register(ConfiguracionTaller)
class ConfiguracionTallerAdmin(admin.ModelAdmin):
    list_display = (
        'taller',
        'tipo_vehiculo',
        'turnos_simultaneos',
        'intervalo_minutos',
        'status'
    )
    list_filter = ('status', 'taller', 'tipo_vehiculo')
    search_fields = ('taller__nombre', 'tipo_vehiculo__nombre')
    ordering = ('taller__nombre', 'tipo_vehiculo__nombre')
    list_editable = ('status', 'turnos_simultaneos', 'intervalo_minutos')

    autocomplete_fields = ['taller', 'tipo_vehiculo']


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'dominio',
        'tipo_vehiculo',
        'get_titular',
        'tiene_gnc',
        'status',
        'created_at'
    )
    list_filter = ('tipo_vehiculo', 'tiene_gnc', 'status', 'created_at')
    search_fields = (
        'dominio',
        'cliente__nombre',
        'cliente__apellido',
        'cliente__dni'
    )
    ordering = ('dominio',)
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')

    autocomplete_fields = ['cliente', 'tipo_vehiculo']

    fieldsets = (
        ('Información del Vehículo', {
            'fields': ('dominio', 'tipo_vehiculo', 'tiene_gnc')
        }),
        ('Titular (Cliente)', {
            'fields': ('cliente',)
        }),
        ('Estado', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

    def get_titular(self, obj):
        return f"{obj.cliente.apellido}, {obj.cliente.nombre} (DNI: {obj.cliente.dni})"
    get_titular.short_description = 'Titular'
    get_titular.admin_order_field = 'cliente__apellido'
