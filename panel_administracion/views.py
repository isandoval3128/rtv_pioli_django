from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from turnero.models import Turno, HistorialTurno
from clientes.models import Cliente
from talleres.models import Taller, TipoVehiculo, Vehiculo, ConfiguracionTaller


@login_required(login_url='/panel/login/')
def home(request):
    """Vista principal del panel de administración"""
    from turnero.models import Turno
    from clientes.models import Cliente
    from talleres.models import Taller

    # Estadísticas básicas
    hoy = timezone.now().date()

    context = {
        'turnos_pendientes': Turno.objects.filter(estado='PENDIENTE').count(),
        'turnos_hoy': Turno.objects.filter(fecha=hoy).count(),
        'clientes_total': Cliente.objects.count(),
        'talleres_activos': Taller.objects.filter(status=True).count(),
    }

    return render(request, 'panel/home.html', context)


def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    return redirect('panel_login')


# ============================================
# GESTIÓN DE TURNOS
# ============================================

@login_required(login_url='/panel/login/')
def gestion_turnos(request):
    """Vista principal de gestión de turnos"""
    context = {
        'titulo': 'Gestión de Turnos',
        'talleres': Taller.objects.filter(status=True),
    }
    return render(request, 'panel/gestion_turnos.html', context)


@login_required(login_url='/panel/login/')
def gestion_turnos_ajax(request):
    """Retorna los turnos en formato JSON para DataTables"""
    if request.method == 'POST':
        # Filtros
        filtro_codigo = request.POST.get('filtro_codigo', '').strip()
        filtro_estado = request.POST.get('filtro_estado', '')
        filtro_taller = request.POST.get('filtro_taller', '')
        filtro_cliente = request.POST.get('filtro_cliente', '').strip()
        filtro_dominio = request.POST.get('filtro_dominio', '').strip()
        filtro_fecha_desde = request.POST.get('filtro_fecha_desde', '')
        filtro_fecha_hasta = request.POST.get('filtro_fecha_hasta', '')

        # Query base
        turnos = Turno.objects.select_related('cliente', 'vehiculo', 'taller', 'tipo_vehiculo').all()

        # Aplicar filtros
        if filtro_codigo:
            turnos = turnos.filter(codigo__icontains=filtro_codigo)
        if filtro_estado:
            turnos = turnos.filter(estado=filtro_estado)
        if filtro_taller:
            turnos = turnos.filter(taller_id=filtro_taller)
        if filtro_cliente:
            turnos = turnos.filter(
                Q(cliente__dni__icontains=filtro_cliente) |
                Q(cliente__nombre__icontains=filtro_cliente) |
                Q(cliente__apellido__icontains=filtro_cliente)
            )
        if filtro_dominio:
            turnos = turnos.filter(vehiculo__dominio__icontains=filtro_dominio)
        if filtro_fecha_desde:
            turnos = turnos.filter(fecha__gte=filtro_fecha_desde)
        if filtro_fecha_hasta:
            turnos = turnos.filter(fecha__lte=filtro_fecha_hasta)

        # Ordenar por fecha de creación descendente (últimos turnos cargados primero)
        turnos = turnos.order_by('-created_at')[:500]

        # Construir respuesta
        data = []
        for t in turnos:
            data.append({
                'id': t.id,
                'codigo': t.codigo,
                'cliente_nombre': f"{t.cliente.nombre} {t.cliente.apellido}",
                'cliente_dni': t.cliente.dni,
                'vehiculo_dominio': t.vehiculo.dominio,
                'tipo_vehiculo': t.tipo_vehiculo.nombre,
                'taller_nombre': t.taller.get_nombre(),
                'fecha': str(t.fecha),
                'hora_inicio': t.hora_inicio.strftime('%H:%M'),
                'hora_fin': t.hora_fin.strftime('%H:%M'),
                'estado': t.estado,
                'email_enviado': t.email_enviado,
                'whatsapp_enviado': t.whatsapp_enviado,
            })

        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_form(request):
    """Retorna el formulario para crear/editar turno"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        turno = None

        if pk:
            turno = get_object_or_404(Turno, pk=pk)

        context = {
            'titulo': 'Editar Turno' if turno else 'Nuevo Turno',
            'turno': turno,
            'clientes': Cliente.objects.all().order_by('apellido', 'nombre'),
            'talleres': Taller.objects.filter(status=True),
            'tipos_vehiculo': TipoVehiculo.objects.filter(status=True),
            'fecha_minima': timezone.now().date(),
        }

        html_form = render_to_string('panel/gestion_turnos_form.html', context, request=request)
        return JsonResponse({'html_form': html_form})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_ver(request):
    """Retorna los detalles del turno para el modal VerMas"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        turno = get_object_or_404(Turno, pk=pk)

        context = {
            'turno': turno,
        }

        html_form = render_to_string('panel/gestion_turnos_VerMas.html', context, request=request)
        return JsonResponse({'html_form': html_form})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_guardar(request):
    """Guarda un turno nuevo o editado"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        cliente_id = request.POST.get('cliente')
        vehiculo_id = request.POST.get('vehiculo')
        taller_id = request.POST.get('taller')
        tipo_vehiculo_id = request.POST.get('tipo_vehiculo')
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        estado = request.POST.get('estado', 'PENDIENTE')
        observaciones = request.POST.get('observaciones', '')

        # ============================================
        # Validaciones de fecha y hora del taller
        # ============================================
        try:
            from datetime import datetime, date, time

            taller = Taller.objects.get(pk=taller_id)
            fecha_turno = datetime.strptime(fecha, '%Y-%m-%d').date()
            hora_inicio_turno = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fin_turno = datetime.strptime(hora_fin, '%H:%M').time()

            # Mapeo de días de la semana
            dias_semana = {
                0: 'lunes',
                1: 'martes',
                2: 'miercoles',
                3: 'jueves',
                4: 'viernes',
                5: 'sabado',
                6: 'domingo'
            }

            # Validar día de atención
            dia_semana = fecha_turno.weekday()
            dia_texto = dias_semana[dia_semana]

            if taller.dias_atencion and len(taller.dias_atencion) > 0:
                if not taller.dias_atencion.get(dia_texto, False):
                    return JsonResponse({
                        'success': False,
                        'error': f'El taller no atiende los días {dia_texto.capitalize()}'
                    })

            # Validar fechas no laborables
            if taller.fechas_no_laborables and len(taller.fechas_no_laborables) > 0:
                if fecha in taller.fechas_no_laborables:
                    return JsonResponse({
                        'success': False,
                        'error': 'Esta fecha está marcada como no laborable (feriado o día especial)'
                    })

            # Validar horario de apertura
            if taller.horario_apertura and hora_inicio_turno < taller.horario_apertura:
                return JsonResponse({
                    'success': False,
                    'error': f'El taller abre a las {taller.horario_apertura.strftime("%H:%M")} hs'
                })

            # Validar horario de cierre
            if taller.horario_cierre:
                if hora_inicio_turno >= taller.horario_cierre:
                    return JsonResponse({
                        'success': False,
                        'error': f'El taller cierra a las {taller.horario_cierre.strftime("%H:%M")} hs'
                    })
                if hora_fin_turno > taller.horario_cierre:
                    return JsonResponse({
                        'success': False,
                        'error': f'El turno debe finalizar antes de las {taller.horario_cierre.strftime("%H:%M")} hs'
                    })

            # Validar que hora fin sea mayor a hora inicio
            if hora_fin_turno <= hora_inicio_turno:
                return JsonResponse({
                    'success': False,
                    'error': 'La hora de fin debe ser mayor a la hora de inicio'
                })

        except Taller.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Taller no encontrado'})
        except ValueError as e:
            return JsonResponse({'success': False, 'error': f'Error en formato de fecha/hora: {str(e)}'})

        try:
            if pk:
                # Editar turno existente
                turno = get_object_or_404(Turno, pk=pk)

                # Verificar si ya existe otro turno con la misma combinación (excluyendo el actual)
                turno_existente = Turno.objects.filter(
                    taller_id=taller_id,
                    fecha=fecha,
                    hora_inicio=hora_inicio
                ).exclude(pk=pk).first()

                if turno_existente:
                    return JsonResponse({
                        'success': False,
                        'error': f'Ya existe un turno para ese taller, fecha y hora ({turno_existente.codigo})'
                    })

                turno.cliente_id = cliente_id
                turno.vehiculo_id = vehiculo_id
                turno.taller_id = taller_id
                turno.tipo_vehiculo_id = tipo_vehiculo_id
                turno.fecha = fecha
                turno.hora_inicio = hora_inicio
                turno.hora_fin = hora_fin
                turno.estado = estado
                turno.observaciones = observaciones

                # Checkboxes de notificaciones
                turno.email_enviado = request.POST.get('email_enviado') == 'on'
                turno.whatsapp_enviado = request.POST.get('whatsapp_enviado') == 'on'
                turno.recordatorio_enviado = request.POST.get('recordatorio_enviado') == 'on'

                turno.save()

                # Registrar en historial
                HistorialTurno.objects.create(
                    turno=turno,
                    accion='Modificación',
                    descripcion=f'Turno modificado por {request.user.username}',
                    usuario=request.user,
                    ip_address=get_client_ip(request)
                )

                return JsonResponse({'success': True, 'message': 'Turno actualizado correctamente'})
            else:
                # Verificar si ya existe un turno con la misma combinación
                turno_existente = Turno.objects.filter(
                    taller_id=taller_id,
                    fecha=fecha,
                    hora_inicio=hora_inicio
                ).first()

                if turno_existente:
                    return JsonResponse({
                        'success': False,
                        'error': f'Ya existe un turno para ese taller, fecha y hora ({turno_existente.codigo})'
                    })

                # Crear nuevo turno
                turno = Turno.objects.create(
                    cliente_id=cliente_id,
                    vehiculo_id=vehiculo_id,
                    taller_id=taller_id,
                    tipo_vehiculo_id=tipo_vehiculo_id,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    estado=estado,
                    observaciones=observaciones,
                    created_by=request.user
                )

                # Registrar en historial
                HistorialTurno.objects.create(
                    turno=turno,
                    accion='Creación',
                    descripcion=f'Turno creado desde el panel por {request.user.username}',
                    usuario=request.user,
                    ip_address=get_client_ip(request)
                )

                return JsonResponse({'success': True, 'message': 'Turno creado correctamente'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_cancelar(request):
    """Cancela un turno"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        turno = get_object_or_404(Turno, pk=pk)

        try:
            turno.estado = 'CANCELADO'
            turno.save()

            # Registrar en historial
            HistorialTurno.objects.create(
                turno=turno,
                accion='Cancelación',
                descripcion=f'Turno cancelado desde el panel por {request.user.username}',
                usuario=request.user,
                ip_address=get_client_ip(request)
            )

            return JsonResponse({'success': True, 'message': 'Turno cancelado correctamente'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_reenviar_email(request):
    """Reenvía el email de confirmación del turno usando el formato HTML profesional"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        turno = get_object_or_404(Turno, pk=pk)

        try:
            # Usar la función utilitaria centralizada
            from turnero.utils import enviar_email_turno

            success, message = enviar_email_turno(turno, motivo='confirmacion')

            if success:
                # Marcar como enviado
                turno.email_enviado = True
                turno.save()

                # Registrar en historial
                HistorialTurno.objects.create(
                    turno=turno,
                    accion='Email reenviado',
                    descripcion=f'Email de confirmación reenviado por {request.user.username} a {turno.cliente.email}',
                    usuario=request.user,
                    ip_address=get_client_ip(request)
                )

                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'error': message})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_whatsapp(request):
    """Genera el enlace de WhatsApp para el turno"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        turno = get_object_or_404(Turno, pk=pk)

        try:
            celular = turno.cliente.celular
            if not celular:
                return JsonResponse({'success': False, 'error': 'El cliente no tiene celular registrado'})

            # Limpiar número de teléfono
            celular = ''.join(filter(str.isdigit, celular))
            if not celular.startswith('54'):
                celular = '54' + celular

            # Mensaje de WhatsApp
            mensaje = f"""*Recordatorio de Turno RTV*

Código: {turno.codigo}
Fecha: {turno.fecha.strftime('%d/%m/%Y')}
Hora: {turno.hora_inicio.strftime('%H:%M')} hs
Taller: {turno.taller.get_nombre()}
Vehículo: {turno.vehiculo.dominio}

Por favor, llegue 10 minutos antes de su turno.

¡Gracias por confiar en nosotros!"""

            # URL de WhatsApp
            import urllib.parse
            whatsapp_url = f"https://wa.me/{celular}?text={urllib.parse.quote(mensaje)}"

            # Marcar como enviado
            turno.whatsapp_enviado = True
            turno.save()

            # Registrar en historial
            HistorialTurno.objects.create(
                turno=turno,
                accion='WhatsApp generado',
                descripcion=f'Enlace de WhatsApp generado por {request.user.username}',
                usuario=request.user,
                ip_address=get_client_ip(request)
            )

            return JsonResponse({'success': True, 'whatsapp_url': whatsapp_url})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_turnos_imprimir(request, pk):
    """Vista para imprimir el comprobante del turno"""
    turno = get_object_or_404(Turno, pk=pk)

    context = {
        'turno': turno,
    }

    return render(request, 'panel/gestion_turnos_imprimir.html', context)


@login_required(login_url='/panel/login/')
def obtener_vehiculos_cliente(request):
    """Retorna los vehículos de un cliente en formato JSON"""
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente_id', '')

            if not cliente_id:
                return JsonResponse({'vehiculos': [], 'success': True})

            vehiculos = Vehiculo.objects.filter(cliente_id=cliente_id, status=True)

            data = []
            for v in vehiculos:
                # Construir descripción del vehículo
                tipo_nombre = v.tipo_vehiculo.nombre_normalizado if v.tipo_vehiculo else ''

                data.append({
                    'id': v.id,
                    'dominio': v.dominio,
                    'tipo': tipo_nombre,
                    'tiene_gnc': v.tiene_gnc,
                })

            return JsonResponse({'vehiculos': data, 'success': True})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Método no permitido', 'success': False}, status=405)


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================
# CREACIÓN RÁPIDA DE CLIENTE Y VEHÍCULO
# ============================================

@login_required(login_url='/panel/login/')
def guardar_cliente_rapido(request):
    """Guarda un cliente de forma rápida desde el formulario de turnos"""
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip()
        celular = request.POST.get('celular', '').strip()
        domicilio = request.POST.get('domicilio', '').strip()

        if not dni or not nombre or not apellido:
            return JsonResponse({'success': False, 'error': 'DNI, Nombre y Apellido son obligatorios'})

        # Verificar si ya existe un cliente con ese DNI
        if Cliente.objects.filter(dni=dni).exists():
            return JsonResponse({'success': False, 'error': f'Ya existe un cliente con DNI {dni}'})

        try:
            cliente = Cliente.objects.create(
                dni=dni,
                nombre=nombre,
                apellido=apellido,
                email=email if email else None,
                celular=celular if celular else None,
                domicilio=domicilio if domicilio else None,
            )

            return JsonResponse({
                'success': True,
                'cliente': {
                    'id': cliente.id,
                    'dni': cliente.dni,
                    'nombre': cliente.nombre,
                    'apellido': cliente.apellido,
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def guardar_vehiculo_rapido(request):
    """Guarda un vehículo de forma rápida desde el formulario de turnos"""
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id', '')
        dominio = request.POST.get('dominio', '').strip().upper()
        marca = request.POST.get('marca', '').strip()
        modelo = request.POST.get('modelo', '').strip()
        tiene_gnc = request.POST.get('tiene_gnc') == 'on'

        if not cliente_id or not dominio:
            return JsonResponse({'success': False, 'error': 'Cliente y Dominio son obligatorios'})

        # Verificar si ya existe un vehículo con ese dominio
        if Vehiculo.objects.filter(dominio=dominio).exists():
            return JsonResponse({'success': False, 'error': f'Ya existe un vehículo con dominio {dominio}'})

        try:
            vehiculo = Vehiculo.objects.create(
                cliente_id=cliente_id,
                dominio=dominio,
                tiene_gnc=tiene_gnc,
            )

            # Agregar marca y modelo si el modelo los soporta
            if hasattr(vehiculo, 'marca'):
                vehiculo.marca = marca if marca else None
            if hasattr(vehiculo, 'modelo'):
                vehiculo.modelo = modelo if modelo else None
            vehiculo.save()

            return JsonResponse({
                'success': True,
                'vehiculo': {
                    'id': vehiculo.id,
                    'dominio': vehiculo.dominio,
                    'marca': marca,
                    'modelo': modelo,
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def obtener_configuracion_taller(request):
    """Retorna la configuración del taller para validación de turnos"""
    if request.method == 'POST':
        taller_id = request.POST.get('taller_id', '')

        if not taller_id:
            return JsonResponse({'success': False, 'error': 'Taller no especificado'})

        try:
            taller = Taller.objects.get(pk=taller_id)

            # Obtener días de atención
            dias_atencion = taller.dias_atencion or {}

            # Obtener fechas no laborables y normalizar formato a YYYY-MM-DD
            fechas_raw = taller.fechas_no_laborables or []
            fechas_no_laborables = []
            for fecha in fechas_raw:
                if isinstance(fecha, str):
                    # Si ya es string, asegurarse que tenga formato YYYY-MM-DD
                    fechas_no_laborables.append(fecha[:10] if len(fecha) >= 10 else fecha)
                else:
                    # Si es un objeto date/datetime
                    try:
                        fechas_no_laborables.append(fecha.strftime('%Y-%m-%d'))
                    except:
                        fechas_no_laborables.append(str(fecha)[:10])

            # Obtener horarios
            horario_apertura = taller.horario_apertura.strftime('%H:%M') if taller.horario_apertura else '08:00'
            horario_cierre = taller.horario_cierre.strftime('%H:%M') if taller.horario_cierre else '18:00'

            return JsonResponse({
                'success': True,
                'configuracion': {
                    'dias_atencion': dias_atencion,
                    'fechas_no_laborables': fechas_no_laborables,
                    'horario_apertura': horario_apertura,
                    'horario_cierre': horario_cierre,
                }
            })

        except Taller.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Taller no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def obtener_tipos_tramite_taller(request):
    """Retorna los tipos de trámite disponibles para un taller específico"""
    if request.method == 'POST':
        taller_id = request.POST.get('taller_id', '')

        if not taller_id:
            return JsonResponse({'success': False, 'error': 'Taller no especificado'})

        try:
            # Obtener configuraciones activas del taller ordenadas alfabéticamente por nombre
            configuraciones = ConfiguracionTaller.objects.filter(
                taller_id=taller_id,
                status=True,
                tipo_vehiculo__status=True
            ).select_related('tipo_vehiculo').order_by('tipo_vehiculo__nombre')

            tipos_tramite = []
            for config in configuraciones:
                # Obtener el precio (priorizar provincial, luego nacional, luego cajutad)
                precio = config.tipo_vehiculo.precio_provincial or config.tipo_vehiculo.precio_nacional or config.tipo_vehiculo.precio_cajutad or 0

                tipos_tramite.append({
                    'id': config.tipo_vehiculo.id,
                    'nombre': config.tipo_vehiculo.nombre_normalizado,
                    'duracion_minutos': config.tipo_vehiculo.duracion_minutos,
                    'intervalo_minutos': config.intervalo_minutos,
                    'precio': float(precio) if precio else 0,
                })

            return JsonResponse({
                'success': True,
                'tipos_tramite': tipos_tramite
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def obtener_horarios_disponibles(request):
    """Retorna los horarios disponibles para una fecha, taller y tipo de trámite"""
    if request.method == 'POST':
        taller_id = request.POST.get('taller_id', '')
        tipo_vehiculo_id = request.POST.get('tipo_vehiculo_id', '')
        fecha = request.POST.get('fecha', '')
        turno_id = request.POST.get('turno_id', '')  # ID del turno en edición (opcional)

        if not taller_id or not tipo_vehiculo_id or not fecha:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos'})

        try:
            from datetime import datetime, timedelta

            taller = Taller.objects.get(pk=taller_id)
            tipo_vehiculo = TipoVehiculo.objects.get(pk=tipo_vehiculo_id)

            # Obtener configuración del taller para este tipo de trámite
            try:
                config = ConfiguracionTaller.objects.get(
                    taller_id=taller_id,
                    tipo_vehiculo_id=tipo_vehiculo_id,
                    status=True
                )
                intervalo = config.intervalo_minutos
                turnos_simultaneos = config.turnos_simultaneos
            except ConfiguracionTaller.DoesNotExist:
                intervalo = tipo_vehiculo.duracion_minutos or 30
                turnos_simultaneos = 2

            # Horarios del taller
            hora_apertura = taller.horario_apertura
            hora_cierre = taller.horario_cierre

            if not hora_apertura or not hora_cierre:
                return JsonResponse({'success': False, 'error': 'El taller no tiene horarios configurados'})

            # Generar slots de horarios
            horarios = []
            hora_actual = datetime.combine(datetime.strptime(fecha, '%Y-%m-%d').date(), hora_apertura)
            hora_fin_dia = datetime.combine(datetime.strptime(fecha, '%Y-%m-%d').date(), hora_cierre)

            # Obtener turnos ya reservados para esa fecha
            # Si estamos editando un turno, excluirlo de la cuenta
            turnos_query = Turno.objects.filter(
                taller_id=taller_id,
                fecha=fecha,
                estado__in=['PENDIENTE', 'CONFIRMADO', 'EN_CURSO']
            )
            if turno_id:
                turnos_query = turnos_query.exclude(pk=turno_id)
            turnos_reservados = turnos_query.values_list('hora_inicio', flat=True)

            turnos_por_hora = {}
            for hora in turnos_reservados:
                hora_str = hora.strftime('%H:%M')
                turnos_por_hora[hora_str] = turnos_por_hora.get(hora_str, 0) + 1

            while hora_actual < hora_fin_dia:
                hora_str = hora_actual.strftime('%H:%M')
                hora_fin_turno = hora_actual + timedelta(minutes=intervalo)

                # Verificar si el turno termina antes del cierre
                if hora_fin_turno <= hora_fin_dia:
                    # Verificar disponibilidad
                    ocupados = turnos_por_hora.get(hora_str, 0)
                    disponible = ocupados < turnos_simultaneos

                    horarios.append({
                        'hora_inicio': hora_str,
                        'hora_fin': hora_fin_turno.strftime('%H:%M'),
                        'disponible': disponible,
                        'ocupados': ocupados,
                        'capacidad': turnos_simultaneos
                    })

                hora_actual += timedelta(minutes=intervalo)

            return JsonResponse({
                'success': True,
                'horarios': horarios,
                'intervalo_minutos': intervalo
            })

        except Taller.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Taller no encontrado'})
        except TipoVehiculo.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tipo de trámite no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)
