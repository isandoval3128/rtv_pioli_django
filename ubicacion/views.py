from django.shortcuts import render
from django.http import JsonResponse
from .models import Ubicacion


def home(request):
    ubicaciones = Ubicacion.objects.all().order_by('orden', 'nombre')
    # Agrega otros contextos si es necesario
    return render(request, "home.html", {"ubicaciones": ubicaciones})


def get_ubicacion_data(request, ubicacion_id):
    """API endpoint para obtener datos de una ubicación"""
    try:
        ubicacion = Ubicacion.objects.get(id=ubicacion_id)
        return JsonResponse({
            'id': ubicacion.id,
            'nombre': ubicacion.nombre,
            'direccion': ubicacion.direccion,
            'telefono': ubicacion.telefono,
            'email': ubicacion.email,
            'latitud': ubicacion.latitud,
            'longitud': ubicacion.longitud,
            'localidad_id': ubicacion.localidad.id if ubicacion.localidad else None,
            'localidad_nombre': str(ubicacion.localidad) if ubicacion.localidad else None
        })
    except Ubicacion.DoesNotExist:
        return JsonResponse({'error': 'Ubicación no encontrada'}, status=404)
