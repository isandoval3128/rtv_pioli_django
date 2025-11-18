from django.shortcuts import render
from .models import Tarifa
from .utils import excel_to_html

def tarifas_view(request):
    tarifa = Tarifa.objects.first()
    tabla_html = None
    tarifas_list = []
    if tarifa and tarifa.archivo_excel:
        tabla_html = excel_to_html(tarifa.archivo_excel.path)
        from .utils import excel_to_list
        tarifas_list = excel_to_list(tarifa.archivo_excel.path)
        #print("[DEPURACION] tarifas_list:", tarifas_list)
        #print("[DEPURACION] tabla_html:", tabla_html)
    else:
        print("[DEPURACION] No hay tarifa o archivo_excel")
    context = {
        'tarifa': tarifa,
        'tabla_html': tabla_html,
        'tarifas_list': tarifas_list,
    }
    #print("[DEPURACION] context enviado:", context)
    return render(request, 'tarifas.html', context)
