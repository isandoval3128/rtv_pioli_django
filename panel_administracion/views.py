from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from turnero.models import Turno, HistorialTurno
from clientes.models import Cliente
from talleres.models import Taller, TipoVehiculo, Vehiculo, ConfiguracionTaller
from .models import UserProfile, Sector, UserPermission, PasswordResetToken


def get_user_sector(user):
    """
    Obtiene el codigo del sector del usuario.
    Retorna 'ADMINISTRACION' por defecto si no tiene sector asignado o si el codigo es NULL.
    """
    if hasattr(user, 'panel_profile') and user.panel_profile and user.panel_profile.sector:
        # Verificar que el codigo no sea NULL
        codigo = user.panel_profile.sector.codigo
        if codigo:
            return codigo
    return Sector.SECTOR_ADMINISTRACION


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
    # Obtener el sector del usuario (ADMINISTRACION o TALLER)
    user_sector = get_user_sector(request.user)

    context = {
        'titulo': 'Gestión de Turnos',
        'talleres': Taller.objects.filter(status=True),
        'user_origen': user_sector,  # Mantener nombre para compatibilidad con templates
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
        filtro_atendido_por = request.POST.get('filtro_atendido_por', '').strip()

        # Query base
        turnos = Turno.objects.select_related('cliente', 'vehiculo', 'taller', 'tipo_vehiculo', 'atendido_por').all()

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
        if filtro_atendido_por:
            turnos = turnos.filter(
                Q(atendido_por__username__icontains=filtro_atendido_por) |
                Q(atendido_por__first_name__icontains=filtro_atendido_por) |
                Q(atendido_por__last_name__icontains=filtro_atendido_por)
            )

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
                'atendido_por': t.atendido_por.get_full_name() or t.atendido_por.username if t.atendido_por else None,
                'fecha_atencion': t.fecha_atencion.strftime('%d/%m/%Y %H:%M') if t.fecha_atencion else None,
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

        # Obtener el sector del usuario
        user_sector = get_user_sector(request.user)

        context = {
            'turno': turno,
            'user_origen': user_sector,  # Mantener nombre para compatibilidad
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


# ============================================
# ESCANEO DE QR - ATENCION DE TURNOS
# ============================================

@login_required(login_url='/panel/login/')
def escanear_turno(request):
    """Vista principal para escanear QR de turnos"""
    # Obtener el sector del usuario (ADMINISTRACION o TALLER)
    user_sector = get_user_sector(request.user)
    es_taller = user_sector == Sector.SECTOR_TALLER

    context = {
        'titulo': 'Escanear Turno',
        'user_origen': user_sector,
        'es_taller': es_taller,
    }
    return render(request, 'panel/escanear_turno.html', context)


@login_required(login_url='/panel/login/')
def verificar_turno_panel(request):
    """
    Verifica un turno escaneado o ingresado manualmente.
    Comportamiento segun tipo de usuario:
    - ADMINISTRACION: Solo ve la informacion (como el cliente)
    - TALLER: Puede registrar la atencion del turno
    """
    if request.method == 'POST':
        # Aceptar 'busqueda' (del template) o 'codigo'/'dni' por separado
        busqueda = request.POST.get('busqueda', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        dni = request.POST.get('dni', '').strip()
        token = request.POST.get('token', '').strip()

        # Si viene 'busqueda', determinar si es codigo o DNI
        if busqueda and not codigo and not dni:
            busqueda_upper = busqueda.upper()
            # Si empieza con TRN- o tiene formato de codigo, es codigo
            if busqueda_upper.startswith('TRN-') or '-' in busqueda_upper:
                codigo = busqueda_upper
            # Si es solo numeros, es DNI
            elif busqueda.isdigit():
                dni = busqueda
            # Si no, intentar como codigo
            else:
                codigo = busqueda_upper

        # Obtener el sector del usuario
        user_sector = get_user_sector(request.user)

        try:
            turno = None

            # Buscar por codigo de turno
            if codigo:
                # Si viene con token, verificar autenticidad del QR
                if token:
                    if not Turno.verificar_token(codigo, token):
                        return JsonResponse({
                            'success': False,
                            'error': 'QR no valido o manipulado',
                            'tipo_error': 'qr_invalido'
                        })
                turno = Turno.objects.select_related(
                    'cliente', 'vehiculo', 'taller', 'tipo_vehiculo', 'atendido_por'
                ).get(codigo=codigo)

            # Buscar por DNI (plan B)
            elif dni:
                # Buscar turnos del dia para este DNI
                hoy = timezone.now().date()
                turnos = Turno.objects.select_related(
                    'cliente', 'vehiculo', 'taller', 'tipo_vehiculo', 'atendido_por'
                ).filter(
                    cliente__dni=dni,
                    fecha=hoy,
                    estado__in=['PENDIENTE', 'CONFIRMADO']
                ).order_by('hora_inicio')

                if not turnos.exists():
                    return JsonResponse({
                        'success': False,
                        'error': f'No se encontraron turnos para hoy con DNI: {dni}',
                        'tipo_error': 'no_encontrado'
                    })

                # Si hay mas de uno, retornar lista para que elija
                if turnos.count() > 1:
                    lista_turnos = []
                    for t in turnos:
                        lista_turnos.append({
                            'codigo': t.codigo,
                            'hora': t.hora_inicio.strftime('%H:%M'),
                            'vehiculo': t.vehiculo.dominio,
                            'estado': t.get_estado_display()
                        })
                    return JsonResponse({
                        'success': True,
                        'multiples': True,
                        'turnos': lista_turnos
                    })

                turno = turnos.first()

            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Debe ingresar codigo de turno o DNI',
                    'tipo_error': 'sin_datos'
                })

            # Preparar datos del turno
            turno_data = {
                'id': turno.id,
                'codigo': turno.codigo,
                'estado': turno.estado,
                'estado_display': turno.get_estado_display(),
                'fecha': turno.fecha.strftime('%d/%m/%Y'),
                'fecha_iso': turno.fecha.isoformat(),
                'hora': turno.hora_inicio.strftime('%H:%M'),
                'hora_inicio': turno.hora_inicio.strftime('%H:%M'),
                'hora_fin': turno.hora_fin.strftime('%H:%M'),
                'cliente': {
                    'nombre': f"{turno.cliente.nombre} {turno.cliente.apellido}",
                    'dni': turno.cliente.dni,
                    'documento': turno.cliente.dni,
                    'documento_tipo': 'DNI',
                    'celular': turno.cliente.celular or '',
                    'email': turno.cliente.email or '',
                    'iniciales': f"{turno.cliente.nombre[:1]}{turno.cliente.apellido[:1]}".upper()
                },
                'vehiculo': {
                    'dominio': turno.vehiculo.dominio,
                    'marca': turno.vehiculo.marca or '',
                    'modelo': turno.vehiculo.modelo or '',
                },
                'tipo_tramite': turno.tipo_vehiculo.nombre if turno.tipo_vehiculo else '',
                'tipo_vehiculo': turno.tipo_vehiculo.nombre if turno.tipo_vehiculo else '',
                'taller': turno.taller.get_nombre() if turno.taller else '',
                'taller_detalle': {
                    'nombre': turno.taller.get_nombre() if turno.taller else '',
                    'direccion': turno.taller.get_direccion() if turno.taller else '',
                    'localidad': turno.taller.get_localidad().nombre if turno.taller and turno.taller.get_localidad() else '',
                    'telefono': turno.taller.get_telefono() or '' if turno.taller else '',
                },
                'atendido_por': turno.atendido_por.get_full_name() if turno.atendido_por else None,
                'fecha_atencion': turno.fecha_atencion.strftime('%d/%m/%Y %H:%M') if turno.fecha_atencion else None,
                'observaciones': turno.observaciones or '',
            }

            # Determinar estado visual
            hoy = timezone.now().date()
            ahora = timezone.now()

            if turno.estado == 'CANCELADO':
                estado_clase = 'cancelado'
            elif turno.estado in ['COMPLETADO', 'EN_CURSO']:
                estado_clase = 'realizado' if turno.estado == 'COMPLETADO' else 'activo'
            elif turno.fecha < hoy:
                estado_clase = 'vencido'
            elif turno.fecha == hoy:
                estado_clase = 'pendiente-hoy'
            else:
                estado_clase = 'pendiente'

            turno_data['estado_clase'] = estado_clase

            # Calcular si puede registrar atencion
            es_taller = user_sector == Sector.SECTOR_TALLER
            no_fue_atendido = not turno.ya_fue_atendido
            estado_valido = turno.estado in ['PENDIENTE', 'CONFIRMADO']
            es_hoy = turno.fecha == hoy

            puede_registrar = es_taller and no_fue_atendido and estado_valido and es_hoy

            return JsonResponse({
                'success': True,
                'turno': turno_data,
                'user_origen': user_sector,
                'ya_fue_atendido': turno.ya_fue_atendido,
                'puede_registrar_atencion': puede_registrar,
            })

        except Turno.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'No se encontro turno con codigo: {codigo}',
                'tipo_error': 'no_encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'tipo_error': 'error_sistema'
            })

    return JsonResponse({'error': 'Metodo no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def registrar_atencion_turno(request):
    """
    Registra la atencion de un turno (solo para usuarios TALLER)
    """
    if request.method == 'POST':
        turno_id = request.POST.get('turno_id', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()

        # Verificar que el usuario sea del sector TALLER
        user_sector = get_user_sector(request.user)

        if user_sector != Sector.SECTOR_TALLER:
            return JsonResponse({
                'success': False,
                'error': 'Solo usuarios de Taller pueden registrar atencion'
            })

        try:
            # Buscar por ID o por codigo
            if turno_id:
                turno = Turno.objects.get(id=turno_id)
            elif codigo:
                turno = Turno.objects.get(codigo=codigo)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Debe proporcionar ID o codigo del turno'
                })

            # Verificar que el turno pueda ser atendido
            hoy = timezone.now().date()

            if turno.ya_fue_atendido:
                return JsonResponse({
                    'success': False,
                    'error': 'Este turno ya fue atendido anteriormente'
                })

            if turno.estado == 'CANCELADO':
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede atender un turno cancelado'
                })

            if turno.fecha != hoy:
                return JsonResponse({
                    'success': False,
                    'error': 'Solo se pueden atender turnos del dia de hoy'
                })

            # Registrar atencion
            turno.registrar_atencion(
                usuario=request.user,
                ip_address=get_client_ip(request)
            )

            return JsonResponse({
                'success': True,
                'mensaje': f'Turno {turno.codigo} registrado como atendido',
                'turno': {
                    'codigo': turno.codigo,
                    'estado': turno.estado,
                    'estado_display': turno.get_estado_display(),
                    'atendido_por': request.user.get_full_name() or request.user.username,
                    'fecha_atencion': turno.fecha_atencion.strftime('%d/%m/%Y %H:%M')
                }
            })

        except Turno.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'No se encontro turno con codigo: {codigo}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'error': 'Metodo no permitido'}, status=405)


# ============================================
# GESTIÓN DE USUARIOS
# ============================================

@login_required(login_url='/panel/login/')
def gestion_usuarios(request):
    """Vista principal de gestión de usuarios"""
    context = {
        'titulo': 'Gestión de Usuarios',
        'grupos': Group.objects.all().order_by('name'),
        'sectores': Sector.objects.filter(status=True).order_by('nombre'),
        'origenes': UserProfile.ORIGEN_CHOICES,
    }
    return render(request, 'panel/gestion_usuarios.html', context)


@login_required(login_url='/panel/login/')
def gestion_usuarios_ajax(request):
    """Retorna los usuarios en formato JSON para DataTables"""
    if request.method == 'POST':
        # Filtros
        filtro_username = request.POST.get('filtro_username', '').strip()
        filtro_nombre = request.POST.get('filtro_nombre', '').strip()
        filtro_email = request.POST.get('filtro_email', '').strip()
        filtro_grupo = request.POST.get('filtro_grupo', '')
        filtro_sector = request.POST.get('filtro_sector', '')
        filtro_origen = request.POST.get('filtro_origen', '')
        filtro_estado = request.POST.get('filtro_estado', '')

        # Query base - incluir todos los usuarios (activos e inactivos)
        usuarios = User.objects.select_related('panel_profile', 'panel_profile__sector').prefetch_related('groups').all()

        # Aplicar filtros
        if filtro_username:
            usuarios = usuarios.filter(username__icontains=filtro_username)
        if filtro_nombre:
            usuarios = usuarios.filter(
                Q(first_name__icontains=filtro_nombre) |
                Q(last_name__icontains=filtro_nombre)
            )
        if filtro_email:
            usuarios = usuarios.filter(email__icontains=filtro_email)
        if filtro_grupo:
            usuarios = usuarios.filter(groups__id=filtro_grupo)
        if filtro_sector:
            usuarios = usuarios.filter(panel_profile__sector_id=filtro_sector)
        if filtro_origen:
            usuarios = usuarios.filter(panel_profile__origen=filtro_origen)
        if filtro_estado:
            if filtro_estado == 'activo':
                usuarios = usuarios.filter(is_active=True)
            elif filtro_estado == 'inactivo':
                usuarios = usuarios.filter(is_active=False)

        # Ordenar por fecha de creación descendente
        usuarios = usuarios.order_by('-date_joined')[:500]

        # Construir respuesta
        data = []
        for u in usuarios:
            # Obtener grupos
            grupos = list(u.groups.values_list('name', flat=True))

            # Obtener datos del perfil
            sector_codigo = ''
            sector_nombre = ''
            rol = 'GENERAL'
            if hasattr(u, 'panel_profile') and u.panel_profile:
                if u.panel_profile.sector:
                    sector_codigo = u.panel_profile.sector.codigo
                    sector_nombre = u.panel_profile.sector.nombre
                rol = u.panel_profile.origen or 'GENERAL'

            data.append({
                'id': u.id,
                'username': u.username,
                'nombre_completo': u.get_full_name() or u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'grupos': grupos,
                'grupo_principal': grupos[0] if grupos else '-',
                'sector': sector_nombre,
                'sector_codigo': sector_codigo,
                'origen': rol,  # Ahora es el rol/cargo
                'origen_display': dict(UserProfile.ORIGEN_CHOICES).get(rol, rol),
                'is_active': u.is_active,
                'is_staff': u.is_staff,
                'is_superuser': u.is_superuser,
                'last_login': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else 'Nunca',
                'date_joined': u.date_joined.strftime('%d/%m/%Y'),
            })

        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_usuarios_form(request):
    """Retorna el formulario para crear/editar usuario"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        usuario = None

        if pk:
            usuario = get_object_or_404(User, pk=pk)

        context = {
            'titulo': 'Editar Usuario' if usuario else 'Nuevo Usuario',
            'usuario': usuario,
            'grupos': Group.objects.all().order_by('name'),
            'sectores': Sector.objects.filter(status=True).order_by('nombre'),
            'origenes': UserProfile.ORIGEN_CHOICES,
        }

        html_form = render_to_string('panel/gestion_usuarios_Form.html', context, request=request)
        return JsonResponse({'html_form': html_form})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_usuarios_ver(request):
    """Retorna los detalles del usuario para el modal VerMas"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        usuario = get_object_or_404(User, pk=pk)

        context = {
            'usuario': usuario,
        }

        html_form = render_to_string('panel/gestion_usuarios_VerMas.html', context, request=request)
        return JsonResponse({'html_form': html_form})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_usuarios_guardar(request):
    """Guarda un usuario nuevo o editado"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        grupos_ids = request.POST.getlist('grupos')  # Múltiples grupos
        sector_id = request.POST.get('sector', '')
        origen = request.POST.get('origen', 'GENERAL')

        # Validaciones
        if not username:
            return JsonResponse({'success': False, 'error': 'El nombre de usuario es obligatorio'})

        try:
            if pk:
                # Editar usuario existente
                usuario = get_object_or_404(User, pk=pk)

                # Verificar si ya existe otro usuario con el mismo username
                if User.objects.filter(username=username).exclude(pk=pk).exists():
                    return JsonResponse({
                        'success': False,
                        'error': f'Ya existe un usuario con el nombre "{username}"'
                    })

                usuario.username = username
                usuario.first_name = first_name
                usuario.last_name = last_name
                usuario.email = email
                usuario.is_active = is_active
                usuario.is_staff = is_staff

                if password:  # Solo actualizar contraseña si se proporcionó una nueva
                    usuario.set_password(password)

                usuario.save()

                # Actualizar grupos (múltiples)
                usuario.groups.clear()
                if grupos_ids:
                    grupos = Group.objects.filter(pk__in=grupos_ids)
                    usuario.groups.add(*grupos)

                # Actualizar perfil
                if hasattr(usuario, 'panel_profile'):
                    profile = usuario.panel_profile
                else:
                    profile = UserProfile.objects.create(user=usuario)

                profile.origen = origen
                profile.sector_id = sector_id if sector_id else None
                profile.save()

                return JsonResponse({'success': True, 'message': 'Usuario actualizado correctamente'})
            else:
                # Verificar si ya existe un usuario con el mismo username
                if User.objects.filter(username=username).exists():
                    return JsonResponse({
                        'success': False,
                        'error': f'Ya existe un usuario con el nombre "{username}"'
                    })

                if not password:
                    return JsonResponse({'success': False, 'error': 'La contraseña es obligatoria para nuevos usuarios'})

                # Crear nuevo usuario
                usuario = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    is_active=is_active,
                    is_staff=is_staff,
                )

                # Agregar a grupos (múltiples)
                if grupos_ids:
                    grupos = Group.objects.filter(pk__in=grupos_ids)
                    usuario.groups.add(*grupos)

                # Crear/actualizar perfil
                if hasattr(usuario, 'panel_profile'):
                    profile = usuario.panel_profile
                else:
                    profile = UserProfile.objects.create(user=usuario)

                profile.origen = origen
                profile.sector_id = sector_id if sector_id else None
                profile.save()

                return JsonResponse({'success': True, 'message': 'Usuario creado correctamente'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_usuarios_imprimir(request, pk):
    """Vista para imprimir la información del usuario"""
    usuario = get_object_or_404(User, pk=pk)

    context = {
        'usuario': usuario,
    }

    return render(request, 'panel/gestion_usuarios_imprimir.html', context)


@login_required(login_url='/panel/login/')
def gestion_usuarios_reset_password(request):
    """Envía enlace de restablecimiento de contraseña por email"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        usuario = get_object_or_404(User, pk=pk)

        try:
            # Verificar que el usuario tenga email
            if not usuario.email:
                return JsonResponse({
                    'success': False,
                    'error': 'El usuario no tiene un correo electrónico registrado'
                })

            # Generar token de restablecimiento
            reset_token = PasswordResetToken.generate_token(usuario, expiration_hours=24)

            # Enviar email con enlace
            from django.core.mail import EmailMultiAlternatives
            from turnero.utils import get_email_connection

            try:
                # Obtener conexión de email configurada
                connection, email_config = get_email_connection()

                if not connection or not email_config:
                    return JsonResponse({
                        'success': False,
                        'error': 'No hay configuración de correo electrónico'
                    })

                # Construir URL de restablecimiento
                reset_url = request.build_absolute_uri(f'/panel/restablecer-password/{reset_token.token}/')

                # Generar contenido del email
                nombre_usuario = usuario.get_full_name() or usuario.username
                from_email = email_config.default_from_email or email_config.email_host_user

                # Contenido texto plano
                texto = f"""
Hola {nombre_usuario},

Has solicitado restablecer tu contraseña en el Sistema RTV Pioli.

Para crear una nueva contraseña, haz clic en el siguiente enlace:

{reset_url}

Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo.

Saludos,
Sistema RTV Pioli
"""

                # Contenido HTML profesional
                html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; margin: 0;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: #13304D; color: white; padding: 25px; text-align: center;">
            <h1 style="margin: 0; font-size: 22px;">Restablecer Contraseña</h1>
        </div>
        <div style="padding: 30px;">
            <p style="color: #333; font-size: 16px;">Hola <strong>{nombre_usuario}</strong>,</p>
            <p style="color: #666; font-size: 14px;">Has solicitado restablecer tu contraseña en el Sistema RTV Pioli.</p>
            <p style="color: #666; font-size: 14px;">Haz clic en el siguiente botón para crear una nueva contraseña:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="display: inline-block; background: #13304D; color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px;">Restablecer Contraseña</a>
            </div>
            <p style="color: #999; font-size: 12px;">O copia y pega este enlace en tu navegador:</p>
            <p style="background: #f8f9fa; padding: 10px; border-radius: 4px; word-break: break-all; font-size: 12px; color: #666;">{reset_url}</p>
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 20px 0; border-radius: 4px;">
                <p style="margin: 0; color: #856404; font-size: 13px;"><strong>⏱️ Este enlace expirará en 24 horas.</strong></p>
            </div>
            <p style="color: #999; font-size: 12px;">Si no solicitaste este cambio, puedes ignorar este correo.</p>
        </div>
        <div style="background: #f8f9fa; padding: 15px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee;">
            Sistema RTV Pioli - Mensaje automático
        </div>
    </div>
</body>
</html>
"""

                # Crear y enviar email con HTML
                email = EmailMultiAlternatives(
                    subject='Restablecer Contraseña - Sistema RTV Pioli',
                    body=texto,
                    from_email=from_email,
                    to=[usuario.email],
                    connection=connection
                )
                email.attach_alternative(html, "text/html")
                email.send(fail_silently=False)

                return JsonResponse({
                    'success': True,
                    'message': f'Se ha enviado un enlace de restablecimiento a {usuario.email}'
                })
            except Exception as e:
                # Si falla el email, marcar el token como usado
                reset_token.mark_as_used()
                return JsonResponse({
                    'success': False,
                    'error': f'No se pudo enviar el correo: {str(e)}'
                })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def password_reset_form(request, token):
    """Muestra el formulario para crear nueva contraseña"""
    # Validar token
    reset_token = PasswordResetToken.validate_token(token)

    if not reset_token:
        # Token inválido o expirado
        return render(request, 'panel/password_reset_form.html', {
            'error': 'El enlace ha expirado o no es válido. Solicita un nuevo enlace de restablecimiento.',
            'token_invalido': True
        })

    return render(request, 'panel/password_reset_form.html', {
        'token': token,
        'usuario': reset_token.user
    })


def password_reset_confirm(request):
    """Procesa el cambio de contraseña"""
    if request.method == 'POST':
        token = request.POST.get('token', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validar token
        reset_token = PasswordResetToken.validate_token(token)

        if not reset_token:
            return JsonResponse({
                'success': False,
                'error': 'El enlace ha expirado o no es válido'
            })

        # Validaciones
        if not password or not password_confirm:
            return JsonResponse({
                'success': False,
                'error': 'Debes completar ambos campos de contraseña'
            })

        if password != password_confirm:
            return JsonResponse({
                'success': False,
                'error': 'Las contraseñas no coinciden'
            })

        if len(password) < 6:
            return JsonResponse({
                'success': False,
                'error': 'La contraseña debe tener al menos 6 caracteres'
            })

        try:
            # Cambiar contraseña
            usuario = reset_token.user
            usuario.set_password(password)
            usuario.save()

            # Marcar token como usado
            reset_token.mark_as_used()

            return JsonResponse({
                'success': True,
                'message': 'Tu contraseña ha sido actualizada correctamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/panel/login/')
def gestion_usuarios_toggle(request):
    """Activa o desactiva un usuario"""
    if request.method == 'POST':
        pk = request.POST.get('pk', '')
        usuario = get_object_or_404(User, pk=pk)

        try:
            # Cambiar estado
            usuario.is_active = not usuario.is_active
            usuario.save()

            estado = 'activado' if usuario.is_active else 'desactivado'
            return JsonResponse({
                'success': True,
                'message': f'Usuario {estado} correctamente',
                'is_active': usuario.is_active
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)
