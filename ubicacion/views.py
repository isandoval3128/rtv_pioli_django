from django.shortcuts import render
from .models import Ubicacion

def home(request):
    ubicaciones = Ubicacion.objects.all().order_by('orden', 'nombre')
    # Agrega otros contextos si es necesario
    return render(request, "home.html", {"ubicaciones": ubicaciones})
