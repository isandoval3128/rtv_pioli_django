from django.contrib import admin
from .models import Planta

@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "telefono", "provincia", "horario", "latitud", "longitud")
    search_fields = ("nombre", "direccion", "provincia")
