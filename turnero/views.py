from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Q, Count, Case, When, Value, IntegerField
from clientes.models import Cliente
from territorios.models import Localidad
from talleres.models import Taller, TipoVehiculo, Vehiculo, ConfiguracionTaller
from .models import Turno, HistorialTurno, ReservaTemporal
from .forms import (
    Step1ClienteForm, Step2VehiculoForm, Step3TallerForm,
    Step4FechaHoraForm, Step5ConfirmacionForm, CancelarTurnoForm, BuscarTurnoForm
)
import json


def redirect_with_embedded(request, url_name, **url_kwargs):
    """
    Redirect que preserva el parámetro embedded si está presente en el request.
    Útil para mantener el modo embebido (iframe) a través de los pasos del turnero.
    """
    url = reverse(url_name, kwargs=url_kwargs) if url_kwargs else reverse(url_name)
    # Verificar si viene de modo embebido (GET o POST)
    embedded = request.GET.get('embedded') or request.POST.get('embedded')
    if embedded == '1':
        url += '?embedded=1'
    return HttpResponseRedirect(url)


class TurneroHomeView(TemplateView):
    """Vista principal del sistema de turnos"""
    template_name = 'turnero/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['talleres_count'] = Taller.objects.filter(status=True).count()
        context['tipos_tramite'] = TipoVehiculo.objects.filter(status=True).count()
        return context


class Step1ClienteView(View):
    """Paso 1: Cliente - Búsqueda o creación"""
    template_name = 'turnero/step1_cliente.html'

    def get(self, request):
        form = Step1ClienteForm()
        return render(request, self.template_name, {
            'form': form,
            'step': 1,
            'progress': 20
        })

    def post(self, request):
        form = Step1ClienteForm(request.POST)

        if form.is_valid():
            # Determinar si es búsqueda o creación
            dni_busqueda = form.cleaned_data.get('dni_busqueda')

            if dni_busqueda:
                # Buscar cliente existente
                try:
                    cliente = Cliente.objects.get(dni=dni_busqueda, status=True)
                    request.session['cliente_id'] = cliente.id
                    return redirect_with_embedded(request, 'turnero:step2_vehiculo')
                except Cliente.DoesNotExist:
                    return render(request, self.template_name, {
                        'form': form,
                        'step': 1,
                        'progress': 20,
                        'error': 'No se encontró un cliente con ese DNI. Por favor, complete los datos para crear uno nuevo.'
                    })
            else:
                # Crear nueva persona
                dni = form.cleaned_data.get('dni')
                if not dni:
                    return render(request, self.template_name, {
                        'form': form,
                        'step': 1,
                        'progress': 20,
                        'error': 'Debe ingresar un DNI para buscar o crear un cliente.'
                    })

                # Verificar si ya existe
                if Cliente.objects.filter(dni=dni).exists():
                    cliente = Cliente.objects.get(dni=dni)
                else:
                    # Crear nuevo cliente
                    cliente = Cliente.objects.create(
                        dni=dni,
                        nombre=form.cleaned_data.get('nombre'),
                        apellido=form.cleaned_data.get('apellido'),
                        email=form.cleaned_data.get('email'),
                        celular=form.cleaned_data.get('cel'),
                        localidad=form.cleaned_data.get('localidad'),
                        domicilio=form.cleaned_data.get('domicilio'),
                        status=True,
                        cliente_activo=True,
                        estado_cliente='ACTIVO'
                    )

                request.session['cliente_id'] = cliente.id
                return redirect_with_embedded(request, 'turnero:step2_vehiculo')

        return render(request, self.template_name, {
            'form': form,
            'step': 1,
            'progress': 20
        })


class Step2VehiculoView(View):
    """Paso 2: Vehículo - Búsqueda o creación"""
    template_name = 'turnero/step2_vehiculo.html'

    def get(self, request):
        # Verificar que haya persona en sesión
        if 'cliente_id' not in request.session:
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        form = Step2VehiculoForm()
        cliente = Cliente.objects.get(id=request.session['cliente_id'])

        return render(request, self.template_name, {
            'form': form,
            'step': 2,
            'progress': 40,
            'cliente': cliente
        })

    def post(self, request):
        if 'cliente_id' not in request.session:
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        form = Step2VehiculoForm(request.POST)
        cliente = Cliente.objects.get(id=request.session['cliente_id'])

        print(f"DEBUG Step2 POST - Datos recibidos: {request.POST}")
        print(f"DEBUG Step2 POST - Form valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG Step2 POST - Form errors: {form.errors}")

        if form.is_valid():
            dominio_busqueda = form.cleaned_data.get('dominio_busqueda')

            if dominio_busqueda:
                # Buscar vehículo existente
                try:
                    vehiculo = Vehiculo.objects.get(dominio=dominio_busqueda.upper(), status=True)
                    request.session['vehiculo_id'] = vehiculo.id
                    # tipo_vehiculo_id se selecciona en Step3
                    return redirect_with_embedded(request, 'turnero:step3_taller')
                except Vehiculo.DoesNotExist:
                    return render(request, self.template_name, {
                        'form': form,
                        'step': 2,
                        'progress': 40,
                        'cliente': cliente,
                        'error': 'No se encontró un vehículo con ese dominio. Por favor, complete los datos para crear uno nuevo.'
                    })
            else:
                # Crear nuevo vehículo
                dominio = form.cleaned_data.get('dominio')
                if not dominio:
                    return render(request, self.template_name, {
                        'form': form,
                        'step': 2,
                        'progress': 40,
                        'cliente': cliente,
                        'error': 'Debe ingresar un dominio para buscar o crear un vehículo.'
                    })

                tipo_vehiculo = form.cleaned_data.get('tipo_vehiculo')
                # Si no se seleccionó tipo_vehiculo, usar el DEFAULT (seccion oculta en frontend)
                if not tipo_vehiculo:
                    # Buscar el tipo DEFAULT creado por la migracion
                    tipo_vehiculo = TipoVehiculo.objects.filter(codigo_tramite='DEFAULT', status=True).first()
                    # Si no existe el DEFAULT, usar cualquier tipo activo como fallback
                    if not tipo_vehiculo:
                        tipo_vehiculo = TipoVehiculo.objects.filter(status=True).first()
                    if not tipo_vehiculo:
                        return render(request, self.template_name, {
                            'form': form,
                            'step': 2,
                            'progress': 40,
                            'cliente': cliente,
                            'error': 'No hay tipos de trámite configurados. Contacte al administrador.'
                        })

                # Verificar si ya existe
                if Vehiculo.objects.filter(dominio=dominio.upper()).exists():
                    vehiculo = Vehiculo.objects.get(dominio=dominio.upper())
                else:
                    vehiculo = Vehiculo.objects.create(
                        dominio=dominio.upper(),
                        tipo_vehiculo=tipo_vehiculo,
                        cliente=cliente,
                        tiene_gnc=form.cleaned_data.get('tiene_gnc', False),
                        status=True
                    )

                request.session['vehiculo_id'] = vehiculo.id
                # tipo_vehiculo_id se selecciona en Step3
                return redirect_with_embedded(request, 'turnero:step3_taller')

        return render(request, self.template_name, {
            'form': form,
            'step': 2,
            'progress': 40,
            'cliente': cliente
        })


class Step3TallerView(View):
    """Paso 3: Selección de taller y tipo de trámite"""
    template_name = 'turnero/step3_taller.html'

    def get(self, request):
        if 'cliente_id' not in request.session or 'vehiculo_id' not in request.session:
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        cliente = Cliente.objects.get(id=request.session['cliente_id'])
        vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])

        # Obtener todos los talleres activos que tienen configuración de trámites
        # Ordenar: Palpalá (ID=1) primero, luego Libertador (ID=2)
        talleres = Taller.objects.filter(
            status=True,
            configuraciones__status=True,
            configuraciones__tipo_vehiculo__status=True
        ).distinct().annotate(
            orden_personalizado=Case(
                When(id=1, then=Value(1)),  # Palpalá
                When(id=2, then=Value(2)),  # Libertador
                default=Value(3),
                output_field=IntegerField()
            )
        ).order_by('orden_personalizado', 'nombre')

        form = Step3TallerForm()
        form.fields['taller'].queryset = talleres

        return render(request, self.template_name, {
            'form': form,
            'step': 3,
            'progress': 60,
            'cliente': cliente,
            'vehiculo': vehiculo,
            'talleres': talleres
        })

    def post(self, request):
        if 'cliente_id' not in request.session or 'vehiculo_id' not in request.session:
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        taller_id = request.POST.get('taller')
        tipo_vehiculo_id = request.POST.get('tipo_vehiculo')

        # Validar que se hayan seleccionado ambos
        if not taller_id or not tipo_vehiculo_id:
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])
            talleres = Taller.objects.filter(
                status=True,
                configuraciones__status=True,
                configuraciones__tipo_vehiculo__status=True
            ).distinct().annotate(
                orden_personalizado=Case(
                    When(id=1, then=Value(1)),  # Palpalá
                    When(id=2, then=Value(2)),  # Libertador
                    default=Value(3),
                    output_field=IntegerField()
                )
            ).order_by('orden_personalizado', 'nombre')

            return render(request, self.template_name, {
                'form': Step3TallerForm(),
                'step': 3,
                'progress': 60,
                'cliente': cliente,
                'vehiculo': vehiculo,
                'talleres': talleres,
                'error': 'Debes seleccionar un taller y un tipo de trámite'
            })

        try:
            taller = Taller.objects.get(id=taller_id, status=True)
            tipo_vehiculo = TipoVehiculo.objects.get(id=tipo_vehiculo_id, status=True)

            # Verificar que el taller tenga configuración para este tipo de trámite
            if not ConfiguracionTaller.objects.filter(
                taller=taller,
                tipo_vehiculo=tipo_vehiculo,
                status=True
            ).exists():
                raise ValueError("El taller no tiene habilitado este tipo de trámite")

            # Guardar en sesión
            request.session['taller_id'] = taller.id
            request.session['tipo_vehiculo_id'] = tipo_vehiculo.id

            return redirect_with_embedded(request, 'turnero:step4_fecha_hora')

        except (Taller.DoesNotExist, TipoVehiculo.DoesNotExist, ValueError) as e:
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])
            talleres = Taller.objects.filter(
                status=True,
                configuraciones__status=True,
                configuraciones__tipo_vehiculo__status=True
            ).distinct().annotate(
                orden_personalizado=Case(
                    When(id=1, then=Value(1)),  # Palpalá
                    When(id=2, then=Value(2)),  # Libertador
                    default=Value(3),
                    output_field=IntegerField()
                )
            ).order_by('orden_personalizado', 'nombre')

            return render(request, self.template_name, {
                'form': Step3TallerForm(),
                'step': 3,
                'progress': 60,
                'cliente': cliente,
                'vehiculo': vehiculo,
                'talleres': talleres,
                'error': str(e)
            })


class Step4FechaHoraView(View):
    """Paso 4: Selección de fecha y hora"""
    template_name = 'turnero/step4_fecha_hora.html'

    def get(self, request):
        if 'taller_id' not in request.session:
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        taller = Taller.objects.get(id=request.session['taller_id'])
        tipo_vehiculo = TipoVehiculo.objects.get(id=request.session['tipo_vehiculo_id'])

        form = Step4FechaHoraForm()

        return render(request, self.template_name, {
            'form': form,
            'step': 4,
            'progress': 80,
            'taller': taller,
            'tipo_vehiculo': tipo_vehiculo
        })

    def post(self, request):
        if 'taller_id' not in request.session:
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        form = Step4FechaHoraForm(request.POST)

        if form.is_valid():
            request.session['fecha'] = form.cleaned_data['fecha'].isoformat()
            request.session['hora_inicio'] = form.cleaned_data['hora_inicio'].strftime('%H:%M')
            return redirect_with_embedded(request, 'turnero:step5_confirmacion')

        taller = Taller.objects.get(id=request.session['taller_id'])
        tipo_vehiculo = TipoVehiculo.objects.get(id=request.session['tipo_vehiculo_id'])

        return render(request, self.template_name, {
            'form': form,
            'step': 4,
            'progress': 80,
            'taller': taller,
            'tipo_vehiculo': tipo_vehiculo
        })


class Step5ConfirmacionView(View):
    """Paso 5: Confirmación y creación del turno"""
    template_name = 'turnero/step5_confirmacion.html'

    def generar_captcha(self):
        """Genera una pregunta matemática simple para el CAPTCHA"""
        import random
        operaciones = [
            ('+', lambda a, b: a + b),
            ('-', lambda a, b: a - b),
            ('×', lambda a, b: a * b),
        ]
        operacion, func = random.choice(operaciones)

        if operacion == '×':
            # Para multiplicación usamos números más pequeños
            num1 = random.randint(2, 9)
            num2 = random.randint(2, 9)
        elif operacion == '-':
            # Para resta, aseguramos resultado positivo
            num1 = random.randint(10, 20)
            num2 = random.randint(1, num1 - 1)
        else:
            # Para suma
            num1 = random.randint(5, 15)
            num2 = random.randint(5, 15)

        respuesta = func(num1, num2)
        pregunta = f"¿Cuánto es {num1} {operacion} {num2}?"

        return pregunta, respuesta

    def get(self, request):
        if not all(k in request.session for k in ['cliente_id', 'vehiculo_id', 'taller_id', 'fecha', 'hora_inicio']):
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        cliente = Cliente.objects.get(id=request.session['cliente_id'])
        vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])
        taller = Taller.objects.get(id=request.session['taller_id'])
        tipo_vehiculo = TipoVehiculo.objects.get(id=request.session['tipo_vehiculo_id'])

        fecha = datetime.fromisoformat(request.session['fecha']).date()
        hora_inicio = datetime.strptime(request.session['hora_inicio'], '%H:%M').time()

        form = Step5ConfirmacionForm()

        # Generar CAPTCHA
        captcha_pregunta, captcha_respuesta = self.generar_captcha()
        request.session['captcha_respuesta'] = captcha_respuesta

        return render(request, self.template_name, {
            'form': form,
            'step': 5,
            'progress': 100,
            'cliente': cliente,
            'vehiculo': vehiculo,
            'taller': taller,
            'tipo_vehiculo': tipo_vehiculo,
            'fecha': fecha,
            'hora_inicio': hora_inicio,
            'captcha_pregunta': captcha_pregunta
        })

    def post(self, request):
        if not all(k in request.session for k in ['cliente_id', 'vehiculo_id', 'taller_id', 'fecha', 'hora_inicio']):
            return redirect_with_embedded(request, 'turnero:step1_cliente')

        form = Step5ConfirmacionForm(request.POST)

        # Validar CAPTCHA
        captcha_respuesta_usuario = request.POST.get('captcha_respuesta', '').strip()
        captcha_respuesta_correcta = request.session.get('captcha_respuesta')
        captcha_error = None

        try:
            if not captcha_respuesta_usuario:
                captcha_error = 'Por favor, resolvé la operación matemática.'
            elif captcha_respuesta_correcta is None:
                captcha_error = 'La sesión expiró. Por favor, recargá la página.'
            elif int(captcha_respuesta_usuario) != int(captcha_respuesta_correcta):
                captcha_error = 'La respuesta es incorrecta. Intentá de nuevo.'
        except (ValueError, TypeError):
            captcha_error = 'Ingresá solo números como respuesta.'

        if captcha_error:
            # Regenerar CAPTCHA para el siguiente intento
            captcha_pregunta, nueva_respuesta = self.generar_captcha()
            request.session['captcha_respuesta'] = nueva_respuesta

            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])
            taller = Taller.objects.get(id=request.session['taller_id'])
            tipo_vehiculo = TipoVehiculo.objects.get(id=request.session['tipo_vehiculo_id'])
            fecha = datetime.fromisoformat(request.session['fecha']).date()
            hora_inicio = datetime.strptime(request.session['hora_inicio'], '%H:%M').time()

            return render(request, self.template_name, {
                'form': form,
                'step': 5,
                'progress': 100,
                'cliente': cliente,
                'vehiculo': vehiculo,
                'taller': taller,
                'tipo_vehiculo': tipo_vehiculo,
                'fecha': fecha,
                'hora_inicio': hora_inicio,
                'captcha_pregunta': captcha_pregunta,
                'captcha_error': captcha_error
            })

        if form.is_valid():
            # Crear el turno
            cliente = Cliente.objects.get(id=request.session['cliente_id'])
            vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])
            taller = Taller.objects.get(id=request.session['taller_id'])
            tipo_vehiculo = TipoVehiculo.objects.get(id=request.session['tipo_vehiculo_id'])

            fecha = datetime.fromisoformat(request.session['fecha']).date()
            hora_inicio = datetime.strptime(request.session['hora_inicio'], '%H:%M').time()

            # Obtener session_key
            session_key = request.session.session_key

            # Limpiar reservas temporales expiradas
            ReservaTemporal.limpiar_expiradas()

            # Verificar disponibilidad final antes de crear el turno
            try:
                config = ConfiguracionTaller.objects.get(taller=taller, tipo_vehiculo=tipo_vehiculo)

                # Contar turnos existentes
                turnos_en_hora = Turno.objects.filter(
                    taller=taller,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    tipo_vehiculo=tipo_vehiculo,
                    estado__in=['PENDIENTE', 'CONFIRMADO']
                ).count()

                if turnos_en_hora >= config.turnos_simultaneos:
                    # Ya no hay disponibilidad, redirigir al paso 4
                    from django.contrib import messages
                    messages.error(request, 'Lo sentimos, el horario seleccionado ya no está disponible. Por favor, seleccione otro horario.')
                    return redirect_with_embedded(request, 'turnero:step4_fecha_hora')

            except ConfiguracionTaller.DoesNotExist:
                config = None  # Continuar si no hay configuración específica

            # Calcular hora de fin usando el intervalo de la configuración del taller
            # Si no hay configuración, usar el duracion_minutos del tipo de vehículo como fallback
            if config:
                duracion = config.intervalo_minutos
            else:
                duracion = tipo_vehiculo.duracion_minutos
            hora_fin_dt = datetime.combine(fecha, hora_inicio) + timedelta(minutes=duracion)
            hora_fin = hora_fin_dt.time()

            turno = Turno.objects.create(
                vehiculo=vehiculo,
                cliente=cliente,
                taller=taller,
                tipo_vehiculo=tipo_vehiculo,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                estado='PENDIENTE',
                observaciones=form.cleaned_data.get('observaciones', '')
            )

            # Eliminar la reserva temporal de esta sesión (ya se convirtió en turno real)
            if session_key:
                ReservaTemporal.objects.filter(session_key=session_key).delete()

            # Crear historial
            HistorialTurno.objects.create(
                turno=turno,
                accion='CREACION',
                descripcion=f'Turno creado desde la web para {vehiculo.dominio}',
                ip_address=self.get_client_ip(request)
            )

            # Enviar email de confirmación
            try:
                from .utils import enviar_email_turno
                success, message = enviar_email_turno(turno, motivo='confirmacion')
                if success:
                    turno.email_enviado = True
                    turno.save(update_fields=['email_enviado'])
                    HistorialTurno.objects.create(
                        turno=turno,
                        accion='EMAIL_ENVIADO',
                        descripcion=f'Email de confirmación enviado a {cliente.email}',
                        ip_address=self.get_client_ip(request)
                    )
            except Exception as e:
                # Si falla el envío de email, no interrumpir el flujo
                # El turno ya fue creado exitosamente
                pass

            # Limpiar sesión
            for key in ['cliente_id', 'vehiculo_id', 'taller_id', 'tipo_vehiculo_id', 'fecha', 'hora_inicio']:
                if key in request.session:
                    del request.session[key]

            return redirect_with_embedded(request, 'turnero:turno_success', codigo=turno.codigo)

        # Si hay errores, volver a mostrar
        cliente = Cliente.objects.get(id=request.session['cliente_id'])
        vehiculo = Vehiculo.objects.get(id=request.session['vehiculo_id'])
        taller = Taller.objects.get(id=request.session['taller_id'])
        tipo_vehiculo = TipoVehiculo.objects.get(id=request.session['tipo_vehiculo_id'])
        fecha = datetime.fromisoformat(request.session['fecha']).date()
        hora_inicio = datetime.strptime(request.session['hora_inicio'], '%H:%M').time()

        # Regenerar CAPTCHA
        captcha_pregunta, captcha_respuesta = self.generar_captcha()
        request.session['captcha_respuesta'] = captcha_respuesta

        return render(request, self.template_name, {
            'form': form,
            'step': 5,
            'progress': 100,
            'cliente': cliente,
            'vehiculo': vehiculo,
            'taller': taller,
            'tipo_vehiculo': tipo_vehiculo,
            'fecha': fecha,
            'hora_inicio': hora_inicio,
            'captcha_pregunta': captcha_pregunta
        })

    def get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TurnoSuccessView(TemplateView):
    """Vista de éxito tras crear el turno"""
    template_name = 'turnero/turno_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        codigo = kwargs.get('codigo')
        context['turno'] = get_object_or_404(Turno, codigo=codigo)
        return context


class VerificarTurnoView(TemplateView):
    """Vista para verificación del turno al escanear QR - Orientada al personal RTV"""
    template_name = 'turnero/verificar_turno.html'

    def get(self, request, *args, **kwargs):
        codigo = kwargs.get('codigo')
        token = request.GET.get('t', '')

        # Verificar que el token sea válido (seguridad del QR)
        if not Turno.verificar_token(codigo, token):
            # Token inválido - mostrar página de error
            return render(request, 'turnero/verificar_turno_invalido.html', {
                'codigo': codigo,
                'mensaje': 'QR no válido o manipulado'
            })

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        codigo = kwargs.get('codigo')
        turno = get_object_or_404(Turno, codigo=codigo)
        context['turno'] = turno
        context['token_valido'] = True  # Si llegamos aquí, el token es válido

        # Determinar el estado visual del turno
        from datetime import date, datetime
        hoy = date.today()
        ahora = datetime.now().time()

        if turno.estado == 'cancelado':
            context['estado_clase'] = 'cancelado'
            context['estado_icono'] = 'fa-times-circle'
            context['estado_texto'] = 'CANCELADO'
        elif turno.estado == 'realizado':
            context['estado_clase'] = 'realizado'
            context['estado_icono'] = 'fa-check-double'
            context['estado_texto'] = 'REALIZADO'
        elif turno.fecha < hoy:
            context['estado_clase'] = 'vencido'
            context['estado_icono'] = 'fa-calendar-times'
            context['estado_texto'] = 'VENCIDO'
        elif turno.fecha == hoy:
            if turno.hora_inicio <= ahora <= turno.hora_fin:
                context['estado_clase'] = 'activo'
                context['estado_icono'] = 'fa-check-circle'
                context['estado_texto'] = 'TURNO ACTIVO'
            elif ahora < turno.hora_inicio:
                context['estado_clase'] = 'pendiente-hoy'
                context['estado_icono'] = 'fa-clock'
                context['estado_texto'] = 'HOY - PENDIENTE'
            else:
                context['estado_clase'] = 'vencido'
                context['estado_icono'] = 'fa-calendar-times'
                context['estado_texto'] = 'HORARIO PASADO'
        else:
            context['estado_clase'] = 'pendiente'
            context['estado_icono'] = 'fa-calendar-check'
            context['estado_texto'] = 'PENDIENTE'

        return context


# AJAX Views para búsquedas dinámicas

def buscar_persona_ajax(request):
    """Buscar cliente por DNI (AJAX)"""
    dni = request.GET.get('dni', '')

    if not dni:
        return JsonResponse({'found': False})

    try:
        cliente = Cliente.objects.get(dni=dni, status=True)
        return JsonResponse({
            'found': True,
            'data': {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'apellido': cliente.apellido,
                'email': cliente.email or '',
                'cel': cliente.celular or '',
                'localidad_id': cliente.localidad.id if cliente.localidad else None,
                'domicilio': cliente.domicilio or ''
            }
        })
    except Cliente.DoesNotExist:
        return JsonResponse({'found': False})


def buscar_vehiculo_ajax(request):
    """Buscar vehículo por dominio (AJAX)"""
    dominio = request.GET.get('dominio', '').upper()

    if not dominio:
        return JsonResponse({'found': False})

    try:
        vehiculo = Vehiculo.objects.get(dominio=dominio, status=True)

        # Verificar si el vehículo tiene turnos pendientes
        turno_pendiente = Turno.objects.filter(
            vehiculo=vehiculo,
            estado__in=['PENDIENTE', 'CONFIRMADO'],
            fecha__gte=timezone.localtime(timezone.now()).date()
        ).order_by('fecha', 'hora_inicio').first()

        response_data = {
            'found': True,
            'data': {
                'id': vehiculo.id,
                'dominio': vehiculo.dominio,
                'tipo_vehiculo_id': vehiculo.tipo_vehiculo.id,
                'tipo_vehiculo_nombre': vehiculo.tipo_vehiculo.nombre,
                'tiene_gnc': vehiculo.tiene_gnc
            }
        }

        if turno_pendiente:
            response_data['turno_pendiente'] = {
                'id': turno_pendiente.id,
                'codigo': turno_pendiente.codigo,
                'fecha': turno_pendiente.fecha.strftime('%d/%m/%Y'),
                'hora': turno_pendiente.hora_inicio.strftime('%H:%M'),
                'taller_nombre': turno_pendiente.taller.get_nombre(),
                'taller_direccion': turno_pendiente.taller.get_direccion(),
                'tipo_tramite': turno_pendiente.tipo_vehiculo.nombre,
                'estado': turno_pendiente.get_estado_display(),
                'puede_reprogramar': turno_pendiente.puede_reprogramar,
                'cliente_nombre': f"{turno_pendiente.cliente.nombre} {turno_pendiente.cliente.apellido}",
                'cliente_dni': turno_pendiente.cliente.dni,
                'cliente_email': turno_pendiente.cliente.email
            }

        return JsonResponse(response_data)
    except Vehiculo.DoesNotExist:
        return JsonResponse({'found': False})


def obtener_tipos_tramite_taller_ajax(request):
    """Obtener tipos de trámite disponibles para un taller (AJAX)"""
    taller_id = request.GET.get('taller_id')

    if not taller_id:
        return JsonResponse({'error': 'Falta el ID del taller'}, status=400)

    try:
        taller = Taller.objects.get(id=taller_id, status=True)

        # Obtener configuraciones activas del taller
        configuraciones = ConfiguracionTaller.objects.filter(
            taller=taller,
            status=True,
            tipo_vehiculo__status=True
        ).select_related('tipo_vehiculo')

        tipos_tramite = []
        for config in configuraciones:
            tipo = config.tipo_vehiculo
            tipos_tramite.append({
                'id': tipo.id,
                'codigo': tipo.codigo_tramite or '',
                'nombre': tipo.nombre,
                'descripcion': tipo.descripcion or '',
                'duracion': tipo.duracion_minutos,
                'precio_provincial': str(tipo.precio_provincial) if tipo.precio_provincial else None,
                'precio_nacional': str(tipo.precio_nacional) if tipo.precio_nacional else None,
            })

        return JsonResponse({
            'success': True,
            'taller_nombre': taller.get_nombre(),
            'tipos_tramite': tipos_tramite
        })

    except Taller.DoesNotExist:
        return JsonResponse({'error': 'Taller no encontrado'}, status=404)


def obtener_horarios_disponibles_ajax(request):
    """Obtener horarios disponibles para una fecha y taller (AJAX)"""
    taller_id = request.GET.get('taller_id')
    tipo_vehiculo_id = request.GET.get('tipo_vehiculo_id')
    fecha_str = request.GET.get('fecha')

    if not all([taller_id, tipo_vehiculo_id, fecha_str]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        taller = Taller.objects.get(id=taller_id)
        tipo_vehiculo = TipoVehiculo.objects.get(id=tipo_vehiculo_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Obtener configuración
        config = ConfiguracionTaller.objects.get(taller=taller, tipo_vehiculo=tipo_vehiculo)

        # Obtener session_key del usuario actual (para excluir su propia reserva)
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Limpiar reservas temporales expiradas
        ReservaTemporal.limpiar_expiradas()

        # Obtener hora actual en zona horaria de Argentina (configurada en settings.py)
        ahora = timezone.localtime(timezone.now())
        hoy = ahora.date()
        hora_actual_sistema = ahora.time()

        # Generar horarios disponibles
        horarios = []
        hora_actual = datetime.combine(fecha, taller.horario_apertura)
        hora_cierre = datetime.combine(fecha, taller.horario_cierre)

        while hora_actual < hora_cierre:
            hora_time = hora_actual.time()

            # Si la fecha es hoy, filtrar horarios que ya pasaron
            if fecha == hoy and hora_time <= hora_actual_sistema:
                hora_actual += timedelta(minutes=config.intervalo_minutos)
                continue

            # Contar turnos confirmados/pendientes del mismo tipo de vehículo
            turnos_en_hora = Turno.objects.filter(
                taller=taller,
                fecha=fecha,
                hora_inicio=hora_time,
                tipo_vehiculo=tipo_vehiculo,
                estado__in=['PENDIENTE', 'CONFIRMADO']
            ).count()

            # Contar reservas temporales activas (excluyendo la del usuario actual)
            reservas_en_hora = ReservaTemporal.contar_reservas_activas(
                taller=taller,
                tipo_vehiculo=tipo_vehiculo,
                fecha=fecha,
                hora_inicio=hora_time,
                excluir_session=session_key
            )

            # Cupos disponibles = capacidad - turnos confirmados - reservas temporales de otros
            cupos_disponibles = config.turnos_simultaneos - turnos_en_hora - reservas_en_hora

            if cupos_disponibles > 0:
                horarios.append({
                    'hora': hora_actual.strftime('%H:%M'),
                    'disponible': True,
                    'cupos': cupos_disponibles,
                    'total': config.turnos_simultaneos
                })

            hora_actual += timedelta(minutes=config.intervalo_minutos)

        return JsonResponse({'horarios': horarios})

    except (Taller.DoesNotExist, TipoVehiculo.DoesNotExist, ConfiguracionTaller.DoesNotExist):
        return JsonResponse({'error': 'Configuración no encontrada'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)


def reservar_horario_ajax(request):
    """
    Crear una reserva temporal cuando el usuario selecciona un horario.
    Esto evita que dos usuarios seleccionen el mismo slot simultáneamente.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    taller_id = request.POST.get('taller_id')
    tipo_vehiculo_id = request.POST.get('tipo_vehiculo_id')
    fecha_str = request.POST.get('fecha')
    hora_str = request.POST.get('hora')

    if not all([taller_id, tipo_vehiculo_id, fecha_str, hora_str]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        taller = Taller.objects.get(id=taller_id)
        tipo_vehiculo = TipoVehiculo.objects.get(id=tipo_vehiculo_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora = datetime.strptime(hora_str, '%H:%M').time()

        # Obtener o crear session_key
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Obtener configuración para verificar capacidad
        config = ConfiguracionTaller.objects.get(taller=taller, tipo_vehiculo=tipo_vehiculo)

        # Limpiar reservas expiradas
        ReservaTemporal.limpiar_expiradas()

        # Contar turnos confirmados
        turnos_en_hora = Turno.objects.filter(
            taller=taller,
            fecha=fecha,
            hora_inicio=hora,
            tipo_vehiculo=tipo_vehiculo,
            estado__in=['PENDIENTE', 'CONFIRMADO']
        ).count()

        # Contar reservas temporales de OTROS usuarios
        reservas_otros = ReservaTemporal.contar_reservas_activas(
            taller=taller,
            tipo_vehiculo=tipo_vehiculo,
            fecha=fecha,
            hora_inicio=hora,
            excluir_session=session_key
        )

        cupos_disponibles = config.turnos_simultaneos - turnos_en_hora - reservas_otros

        if cupos_disponibles <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Este horario ya no está disponible. Por favor, seleccione otro.'
            })

        # Crear la reserva temporal (10 minutos de duración)
        reserva = ReservaTemporal.crear_o_actualizar(
            taller=taller,
            tipo_vehiculo=tipo_vehiculo,
            fecha=fecha,
            hora_inicio=hora,
            session_key=session_key,
            minutos_expiracion=10
        )

        return JsonResponse({
            'success': True,
            'message': 'Horario reservado temporalmente',
            'expira_en': 10,  # minutos
            'reserva_id': reserva.id
        })

    except (Taller.DoesNotExist, TipoVehiculo.DoesNotExist, ConfiguracionTaller.DoesNotExist):
        return JsonResponse({'error': 'Configuración no encontrada'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': f'Formato inválido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def obtener_fechas_disponibles_ajax(request):
    """Obtener fechas disponibles para el calendario (AJAX)"""
    taller_id = request.GET.get('taller_id')
    tipo_vehiculo_id = request.GET.get('tipo_vehiculo_id')

    if not all([taller_id, tipo_vehiculo_id]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        taller = Taller.objects.get(id=taller_id)
        dias_atencion = taller.dias_atencion

        # Obtener hora actual en zona horaria de Argentina
        ahora = timezone.localtime(timezone.now())
        hoy = ahora.date()
        hora_actual = ahora.time()

        fechas_deshabilitadas = []

        for i in range(60):
            fecha = hoy + timedelta(days=i)
            dia_nombre = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'][fecha.weekday()]

            # Deshabilitar si no atiende ese día de la semana
            if not dias_atencion.get(dia_nombre, False):
                fechas_deshabilitadas.append(fecha.isoformat())
                continue

            # Si es hoy, verificar si aún quedan horarios disponibles
            if fecha == hoy:
                # Si ya pasó el horario de cierre, deshabilitar hoy
                if hora_actual >= taller.horario_cierre:
                    fechas_deshabilitadas.append(fecha.isoformat())
                    continue

                # Verificar si queda al menos un horario disponible hoy
                # (considerando el intervalo de turnos)
                try:
                    tipo_vehiculo = TipoVehiculo.objects.get(id=tipo_vehiculo_id)
                    config = ConfiguracionTaller.objects.get(taller=taller, tipo_vehiculo=tipo_vehiculo)

                    # Buscar el próximo horario disponible
                    hora_iteracion = datetime.combine(fecha, taller.horario_apertura)
                    hora_cierre = datetime.combine(fecha, taller.horario_cierre)
                    hay_horarios_disponibles = False

                    while hora_iteracion < hora_cierre:
                        hora_time = hora_iteracion.time()

                        # Solo considerar horarios que aún no pasaron
                        if hora_time > hora_actual:
                            hay_horarios_disponibles = True
                            break

                        hora_iteracion += timedelta(minutes=config.intervalo_minutos)

                    if not hay_horarios_disponibles:
                        fechas_deshabilitadas.append(fecha.isoformat())
                        continue

                except (TipoVehiculo.DoesNotExist, ConfiguracionTaller.DoesNotExist):
                    # Si no hay configuración, deshabilitar por seguridad
                    pass

        # Agregar fechas no laborables (feriados, vacaciones, etc.)
        if taller.fechas_no_laborables:
            for fecha_str in taller.fechas_no_laborables:
                # Validar que la fecha esté en el rango de los próximos 60 días
                try:
                    from datetime import datetime
                    fecha_no_lab = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    if hoy <= fecha_no_lab <= (hoy + timedelta(days=60)):
                        if fecha_no_lab.isoformat() not in fechas_deshabilitadas:
                            fechas_deshabilitadas.append(fecha_no_lab.isoformat())
                except ValueError:
                    # Si el formato de fecha es inválido, ignorar
                    pass

        return JsonResponse({
            'fechas_deshabilitadas': fechas_deshabilitadas,
            'fecha_minima': hoy.isoformat(),
            'fecha_maxima': (hoy + timedelta(days=60)).isoformat()
        })

    except Taller.DoesNotExist:
        return JsonResponse({'error': 'Taller no encontrado'}, status=404)


def imprimir_turno_publico(request, codigo):
    """Vista pública para imprimir el comprobante del turno"""
    turno = get_object_or_404(Turno, codigo=codigo)

    context = {
        'turno': turno,
    }

    return render(request, 'turnero/imprimir_turno.html', context)


class ConsultarTurnoView(View):
    """Vista para consultar turnos existentes"""
    template_name = 'turnero/consultar_turno.html'

    def get(self, request):
        form = BuscarTurnoForm()
        return render(request, self.template_name, {
            'form': form
        })

    def post(self, request):
        form = BuscarTurnoForm(request.POST)

        if form.is_valid():
            tipo_busqueda = form.cleaned_data['tipo_busqueda']
            valor_busqueda = form.cleaned_data['valor_busqueda'].strip().upper()

            # Buscar turnos según el tipo
            turnos = None
            if tipo_busqueda == 'codigo':
                turnos = Turno.objects.filter(codigo__iexact=valor_busqueda)
            elif tipo_busqueda == 'dominio':
                turnos = Turno.objects.filter(vehiculo__dominio__iexact=valor_busqueda)
            elif tipo_busqueda == 'dni':
                turnos = Turno.objects.filter(cliente__dni=valor_busqueda)

            # Filtrar solo turnos activos (no cancelados ni completados antiguos)
            if turnos:
                turnos = turnos.exclude(estado='CANCELADO').order_by('-fecha', '-hora_inicio')

            return render(request, self.template_name, {
                'form': form,
                'turnos': turnos,
                'tipo_busqueda': tipo_busqueda,
                'valor_busqueda': valor_busqueda
            })

        return render(request, self.template_name, {
            'form': form
        })
