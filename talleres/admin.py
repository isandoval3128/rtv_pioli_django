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


class ConfiguracionMasivaForm(forms.Form):
    """Formulario para configuración masiva de turnos"""
    intervalo_minutos = forms.IntegerField(
        label="Intervalo entre turnos (minutos)",
        min_value=5,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'vIntegerField', 'placeholder': 'Ej: 30'})
    )
    turnos_simultaneos = forms.IntegerField(
        label="Turnos Simultáneos",
        min_value=1,
        max_value=20,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'vIntegerField', 'placeholder': 'Ej: 2'})
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
    change_list_template = 'admin/talleres/configuraciontaller_change_list.html'
    actions = ['configurar_masivamente']

    autocomplete_fields = ['taller', 'tipo_vehiculo']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'sincronizar/',
                self.admin_site.admin_view(self.sincronizar_talleres_tramites),
                name='talleres_configuraciontaller_sincronizar'
            ),
            path(
                'configurar-masivo/',
                self.admin_site.admin_view(self.configurar_masivo_view),
                name='talleres_configuraciontaller_configurar_masivo'
            ),
        ]
        return custom_urls + urls

    @admin.action(description="Configurar Intervalo y Turnos Simultáneos")
    def configurar_masivamente(self, request, queryset):
        """Acción para configurar intervalo y turnos simultáneos de forma masiva"""
        selected = queryset.values_list('pk', flat=True)
        selected_ids = ','.join(str(pk) for pk in selected)
        return redirect(f'configurar-masivo/?ids={selected_ids}')

    def configurar_masivo_view(self, request):
        """Vista para el formulario de configuración masiva"""
        ids = request.GET.get('ids', '')
        if not ids:
            self.message_user(request, "No se seleccionaron elementos.", messages.WARNING)
            return redirect('admin:talleres_configuraciontaller_changelist')

        id_list = [int(pk) for pk in ids.split(',') if pk.isdigit()]
        queryset = ConfiguracionTaller.objects.filter(pk__in=id_list)

        if request.method == 'POST':
            form = ConfiguracionMasivaForm(request.POST)
            if form.is_valid():
                intervalo = form.cleaned_data.get('intervalo_minutos')
                turnos = form.cleaned_data.get('turnos_simultaneos')

                updates = {}
                if intervalo:
                    updates['intervalo_minutos'] = intervalo
                if turnos:
                    updates['turnos_simultaneos'] = turnos

                if updates:
                    updated = queryset.update(**updates)
                    campos = []
                    if intervalo:
                        campos.append(f"Intervalo: {intervalo} min")
                    if turnos:
                        campos.append(f"Turnos Simultáneos: {turnos}")
                    self.message_user(
                        request,
                        f"Se actualizaron {updated} configuraciones. {', '.join(campos)}",
                        messages.SUCCESS
                    )
                else:
                    self.message_user(
                        request,
                        "No se ingresaron valores para actualizar.",
                        messages.WARNING
                    )
                return redirect('admin:talleres_configuraciontaller_changelist')
        else:
            form = ConfiguracionMasivaForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Configuración Masiva de Turnos',
            'opts': self.model._meta,
            'form': form,
            'queryset': queryset,
            'count': queryset.count(),
            'ids': ids,
        }
        return render(request, 'admin/talleres/configuracion_masiva.html', context)

    def sincronizar_talleres_tramites(self, request):
        """
        Sincroniza todos los talleres con todos los tipos de trámite.
        Crea las configuraciones faltantes con valores por defecto.
        """
        if request.method == 'POST':
            talleres = Taller.objects.filter(status=True)
            tipos_tramite = TipoVehiculo.objects.filter(status=True)

            creados = 0
            existentes = 0

            for taller in talleres:
                for tipo in tipos_tramite:
                    config, created = ConfiguracionTaller.objects.get_or_create(
                        taller=taller,
                        tipo_vehiculo=tipo,
                        defaults={
                            'turnos_simultaneos': 2,
                            'intervalo_minutos': tipo.duracion_minutos or 30,
                            'status': True,
                        }
                    )
                    if created:
                        creados += 1
                    else:
                        existentes += 1

            if creados > 0:
                self.message_user(
                    request,
                    f"Sincronización completada: {creados} configuraciones creadas.",
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"No se crearon nuevas configuraciones. {existentes} ya existían.",
                    messages.INFO
                )

            return redirect('admin:talleres_configuraciontaller_changelist')

        # Mostrar página de confirmación
        talleres_count = Taller.objects.filter(status=True).count()
        tipos_count = TipoVehiculo.objects.filter(status=True).count()
        existentes_count = ConfiguracionTaller.objects.count()
        total_posibles = talleres_count * tipos_count
        faltantes = total_posibles - existentes_count

        context = {
            **self.admin_site.each_context(request),
            'title': 'Sincronizar Talleres con Trámites',
            'opts': self.model._meta,
            'talleres_count': talleres_count,
            'tipos_count': tipos_count,
            'existentes_count': existentes_count,
            'total_posibles': total_posibles,
            'faltantes': max(0, faltantes),
        }
        return render(request, 'admin/talleres/sincronizar_configuracion.html', context)


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
