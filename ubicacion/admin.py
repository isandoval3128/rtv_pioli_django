from django.contrib import admin
from .models import Ubicacion

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "telefono", "provincia", "horario", "latitud", "longitud", "orden")
    search_fields = ("nombre", "direccion", "provincia")
