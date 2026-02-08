from django.contrib import admin
from .models import Ubicacion


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "localidad", "telefono", "email", "provincia", "orden")
    search_fields = ("nombre", "direccion", "provincia", "localidad__nombre", "email")
    list_filter = ("provincia", "localidad")
    autocomplete_fields = ["localidad"]
    fieldsets = (
        ("Información Principal", {
            "fields": ("nombre", "orden")
        }),
        ("Ubicación Geográfica", {
            "fields": ("provincia", "localidad", "direccion", "latitud", "longitud")
        }),
        ("Datos de Contacto", {
            "fields": ("telefono", "email", "email_operador", "whatsapp_operador", "horario")
        }),
    )
