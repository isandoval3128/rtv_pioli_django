from django.contrib import admin
from .models import Tarifa

@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ("titulo",)
    search_fields = ("titulo",)
