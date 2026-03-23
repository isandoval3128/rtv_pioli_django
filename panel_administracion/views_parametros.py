from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from talleres.models import Taller, TipoVehiculo, ConfiguracionTaller, FranjaAnulada
import json


@login_required(login_url='/panel/login/')
def gestion_parametros(request):
    """Vista principal de gestión de parámetros del turnero"""
    talleres = Taller.objects.all().order_by('nombre')
    context = {
        'talleres': talleres,
    }
    return render(request, 'panel/gestion_parametros.html', context)


# ============================================
# TALLERES
# ============================================

@login_required(login_url='/panel/login/')
def parametros_talleres_ajax(request):
    """Lista de talleres con sus configuraciones de horario"""
    talleres = Taller.objects.all().order_by('nombre')
    data = []
    for t in talleres:
        data.append({
            'id': t.id,
            'nombre': t.get_nombre(),
            'direccion': t.get_direccion(),
            'telefono': t.get_telefono(),
            'email': t.get_email(),
            'email_operador': t.email_operador or '',
            'whatsapp_operador': t.whatsapp_operador or '',
            'horario_apertura': t.horario_apertura.strftime('%H:%M') if t.horario_apertura else '',
            'horario_cierre': t.horario_cierre.strftime('%H:%M') if t.horario_cierre else '',
            'dias_atencion': t.dias_atencion or {},
            'status': t.status,
        })
    return JsonResponse({'data': data})


@login_required(login_url='/panel/login/')
def parametros_talleres_guardar(request):
    """Guardar configuración de un taller"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    taller_id = request.POST.get('id')
    if not taller_id:
        return JsonResponse({'success': False, 'error': 'ID de taller requerido'}, status=400)

    taller = get_object_or_404(Taller, pk=taller_id)

    taller.horario_apertura = request.POST.get('horario_apertura') or None
    taller.horario_cierre = request.POST.get('horario_cierre') or None
    taller.email_operador = request.POST.get('email_operador', '')
    taller.whatsapp_operador = request.POST.get('whatsapp_operador', '')

    dias_json = request.POST.get('dias_atencion', '')
    if dias_json:
        try:
            taller.dias_atencion = json.loads(dias_json)
        except json.JSONDecodeError:
            pass

    status = request.POST.get('status')
    if status is not None:
        taller.status = status == 'true'

    taller.save()
    return JsonResponse({'success': True, 'message': f'Taller "{taller.get_nombre()}" actualizado correctamente.'})


# ============================================
# TIPOS DE TRÁMITE / VEHÍCULO
# ============================================

@login_required(login_url='/panel/login/')
def parametros_tipos_ajax(request):
    """Lista de tipos de trámite/vehículo"""
    tipos = TipoVehiculo.objects.all().order_by('codigo_tramite')
    data = []
    for t in tipos:
        data.append({
            'id': t.id,
            'codigo_tramite': t.codigo_tramite,
            'nombre': t.nombre,
            'precio_provincial': float(t.precio_provincial) if t.precio_provincial else 0,
            'precio_nacional': float(t.precio_nacional) if t.precio_nacional else 0,
            'precio_cajutad': float(t.precio_cajutad) if t.precio_cajutad else 0,
            'duracion_minutos': t.duracion_minutos,
            'status': t.status,
        })
    return JsonResponse({'data': data})


@login_required(login_url='/panel/login/')
def parametros_tipos_guardar(request):
    """Guardar tipo de trámite/vehículo"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    tipo_id = request.POST.get('id')
    if not tipo_id:
        return JsonResponse({'success': False, 'error': 'ID requerido'}, status=400)

    tipo = get_object_or_404(TipoVehiculo, pk=tipo_id)

    precio_provincial = request.POST.get('precio_provincial')
    if precio_provincial:
        try:
            tipo.precio_provincial = float(precio_provincial)
        except (ValueError, TypeError):
            pass

    precio_nacional = request.POST.get('precio_nacional')
    if precio_nacional:
        try:
            tipo.precio_nacional = float(precio_nacional)
        except (ValueError, TypeError):
            pass

    precio_cajutad = request.POST.get('precio_cajutad')
    if precio_cajutad:
        try:
            tipo.precio_cajutad = float(precio_cajutad)
        except (ValueError, TypeError):
            pass

    duracion = request.POST.get('duracion_minutos')
    if duracion:
        try:
            tipo.duracion_minutos = int(duracion)
        except (ValueError, TypeError):
            pass

    status = request.POST.get('status')
    if status is not None:
        tipo.status = status == 'true'

    tipo.save()
    return JsonResponse({'success': True, 'message': f'Tipo "{tipo.codigo_tramite}" actualizado correctamente.'})


# ============================================
# CONFIGURACIÓN TALLER (Capacidad)
# ============================================

@login_required(login_url='/panel/login/')
def parametros_config_ajax(request):
    """Lista de configuraciones taller-tipo (capacidad y intervalos)"""
    configs = ConfiguracionTaller.objects.select_related('taller', 'tipo_vehiculo').all().order_by('taller__nombre', 'tipo_vehiculo__codigo_tramite')
    data = []
    for c in configs:
        data.append({
            'id': c.id,
            'taller_id': c.taller_id,
            'taller_nombre': c.taller.get_nombre(),
            'tipo_vehiculo_id': c.tipo_vehiculo_id,
            'tipo_codigo': c.tipo_vehiculo.codigo_tramite,
            'tipo_nombre': c.tipo_vehiculo.nombre,
            'turnos_simultaneos': c.turnos_simultaneos,
            'intervalo_minutos': c.intervalo_minutos,
            'status': c.status,
        })
    return JsonResponse({'data': data})


@login_required(login_url='/panel/login/')
def parametros_config_guardar(request):
    """Guardar configuración taller-tipo"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    config_id = request.POST.get('id')
    if not config_id:
        return JsonResponse({'success': False, 'error': 'ID requerido'}, status=400)

    config = get_object_or_404(ConfiguracionTaller, pk=config_id)

    turnos = request.POST.get('turnos_simultaneos')
    if turnos:
        try:
            config.turnos_simultaneos = int(turnos)
        except (ValueError, TypeError):
            pass

    intervalo = request.POST.get('intervalo_minutos')
    if intervalo:
        try:
            config.intervalo_minutos = int(intervalo)
        except (ValueError, TypeError):
            pass

    status = request.POST.get('status')
    if status is not None:
        config.status = status == 'true'

    config.save()
    return JsonResponse({'success': True, 'message': 'Configuración actualizada correctamente.'})


# ============================================
# FECHAS NO LABORABLES
# ============================================

@login_required(login_url='/panel/login/')
def parametros_fechas_ajax(request):
    """Lista de fechas no laborables por taller"""
    taller_id = request.GET.get('taller_id')
    if taller_id:
        talleres = Taller.objects.filter(pk=taller_id)
    else:
        talleres = Taller.objects.all().order_by('nombre')

    data = []
    for t in talleres:
        fechas = t.fechas_no_laborables or []
        data.append({
            'taller_id': t.id,
            'taller_nombre': t.get_nombre(),
            'fechas': fechas,
        })
    return JsonResponse({'data': data})


@login_required(login_url='/panel/login/')
def parametros_fechas_guardar(request):
    """Guardar fechas no laborables de un taller"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    taller_id = request.POST.get('taller_id')
    if not taller_id:
        return JsonResponse({'success': False, 'error': 'ID de taller requerido'}, status=400)

    taller = get_object_or_404(Taller, pk=taller_id)

    fechas_json = request.POST.get('fechas', '[]')
    try:
        taller.fechas_no_laborables = json.loads(fechas_json)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Formato de fechas inválido'}, status=400)

    taller.save()
    return JsonResponse({'success': True, 'message': f'Fechas no laborables de "{taller.get_nombre()}" actualizadas.'})


# ============================================
# FRANJAS ANULADAS
# ============================================

@login_required(login_url='/panel/login/')
def parametros_franjas_ajax(request):
    """Lista de franjas anuladas"""
    taller_id = request.GET.get('taller_id')
    franjas = FranjaAnulada.objects.select_related('taller').all().order_by('-fecha', 'hora_inicio')
    if taller_id:
        franjas = franjas.filter(taller_id=taller_id)

    data = []
    for f in franjas:
        data.append({
            'id': f.id,
            'taller_id': f.taller_id,
            'taller_nombre': f.taller.get_nombre(),
            'fecha': f.fecha.strftime('%Y-%m-%d') if f.fecha else '',
            'hora_inicio': f.hora_inicio.strftime('%H:%M') if f.hora_inicio else '',
            'hora_fin': f.hora_fin.strftime('%H:%M') if f.hora_fin else '',
            'motivo': f.motivo or '',
            'status': f.status,
        })
    return JsonResponse({'data': data})


@login_required(login_url='/panel/login/')
def parametros_franjas_guardar(request):
    """Crear o actualizar franja anulada"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    franja_id = request.POST.get('id')

    if franja_id:
        franja = get_object_or_404(FranjaAnulada, pk=franja_id)
    else:
        franja = FranjaAnulada()

    taller_id = request.POST.get('taller_id')
    if not taller_id:
        return JsonResponse({'success': False, 'error': 'Taller requerido'}, status=400)

    franja.taller_id = taller_id
    franja.fecha = request.POST.get('fecha') or None
    franja.hora_inicio = request.POST.get('hora_inicio') or None
    franja.hora_fin = request.POST.get('hora_fin') or None
    franja.motivo = request.POST.get('motivo', '')

    status = request.POST.get('status')
    franja.status = status == 'true' if status is not None else True

    franja.save()
    return JsonResponse({'success': True, 'message': 'Franja anulada guardada correctamente.'})


@login_required(login_url='/panel/login/')
def parametros_franjas_eliminar(request):
    """Eliminar franja anulada"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    franja_id = request.POST.get('id')
    if not franja_id:
        return JsonResponse({'success': False, 'error': 'ID requerido'}, status=400)

    franja = get_object_or_404(FranjaAnulada, pk=franja_id)
    franja.delete()
    return JsonResponse({'success': True, 'message': 'Franja eliminada correctamente.'})
