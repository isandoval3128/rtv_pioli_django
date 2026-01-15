from django.contrib import admin
from .models import Departamento, Municipio, Localidad


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('nombre', 'codigo')
    ordering = ('nombre',)


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'departamento', 'codigo', 'status', 'created_at')
    list_filter = ('departamento', 'status')
    search_fields = ('nombre', 'codigo', 'departamento__nombre')
    autocomplete_fields = ['departamento']
    ordering = ('departamento__nombre', 'nombre')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'departamento')
        }),
        ('Ubicación', {
            'fields': ('domicilio', 'latitud', 'longitud')
        }),
        ('Control', {
            'fields': ('status',)
        }),
    )


@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'municipio', 'departamento', 'codigo_postal', 'status', 'created_at')
    list_filter = ('departamento', 'municipio', 'status')
    search_fields = ('nombre', 'codigo_postal', 'departamento__nombre', 'municipio__nombre')
    autocomplete_fields = ['departamento', 'municipio']
    ordering = ('departamento__nombre', 'nombre')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo_postal')
        }),
        ('Jerarquía Territorial', {
            'fields': ('departamento', 'municipio'),
            'description': 'Toda localidad debe pertenecer a un Departamento. Opcionalmente puede pertenecer a un Municipio del mismo Departamento.'
        }),
        ('Control', {
            'fields': ('status',)
        }),
    )
