from django.shortcuts import render
from .models import Tarifa
from .utils import excel_to_html

def tarifas_view(request):
    tarifa = Tarifa.objects.first()
    tabla_html = None
    if tarifa and tarifa.archivo_excel:
        tabla_html = excel_to_html(tarifa.archivo_excel.path)
    context = {
        'tarifa': tarifa,
        'tabla_html': tabla_html,
    }
    return render(request, 'tarifas.html', context)
