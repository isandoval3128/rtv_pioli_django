from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Service, PortfolioItem, TimelineEvent, TeamMember, SiteConfiguration
from .forms import ContactForm
import json
from .models import AboutSection
from tarifas.models import Tarifa
from tarifas.utils import excel_to_html
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from .models import EmailConfig
from .models import ContactMessage
from .models import WhatsAppConfig
from ubicacion.models import Ubicacion

def home_view(request):
    """
    Vista principal que muestra toda la página SPA con todas las secciones
    """
    # Obtener configuración del sitio
    site_config = SiteConfiguration.get_config()

    # Obtener todos los datos activos
    services = Service.objects.filter(active=True).order_by('order', 'title')
    # Generar HTML para cada archivo adjunto del servicio
    for service in services:
        service.attachment_html = service.get_attachment_html()
    portfolio_items = PortfolioItem.objects.filter(active=True).order_by('order', 'title')
    timeline_events = TimelineEvent.objects.filter(active=True).order_by('order', 'date')
    team_members = TeamMember.objects.filter(active=True).order_by('order', 'name')

    form = ContactForm()
    
    # Obtener configuración de WhatsApp flotante
    whatsapp_config = WhatsAppConfig.objects.first()

    # Obtener ubicaciones dinámicas
    try:
        ubicaciones = Ubicacion.objects.all()
    except ImportError:
        ubicaciones = []

    # Obtener la tarifa, la tabla HTML y la lista para móviles
    try:
        tarifa = Tarifa.objects.first()
        tabla_html = None
        tarifas_list = []
        if tarifa and tarifa.archivo_excel:
            tabla_html = excel_to_html(tarifa.archivo_excel.path)
            from tarifas.utils import excel_to_list
            tarifas_list = excel_to_list(tarifa.archivo_excel.path)
            #print("[DEPURACION] tarifas_list:", tarifas_list)
    except ImportError:
        tarifa = None
        tabla_html = None
        tarifas_list = []

    about_section = AboutSection.objects.first()

    context = {
        'site_config': site_config,
        'services': services,
        'portfolio_items': portfolio_items,
        'timeline_events': timeline_events,
        'team_members': team_members,
        'form': form,
        'ubicaciones': ubicaciones,
        'tarifa': tarifa,
        'tabla_html': tabla_html,
        'tarifas_list': tarifas_list,
        'about_section': about_section,
        'whatsapp_config': whatsapp_config,
    }

    return render(request, 'home.html', context)

def contact_submit(request):
    """
    Vista para procesar el formulario de contacto
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            subject = f"Nuevo mensaje RTV Pioli Web de {data['name']}"
            body = (
                f"Has recibido un nuevo mensaje de contacto desde la web:\n\n"
                f"Nombre: {data['name']}\n"
                f"Email: {data['email']}\n"
                f"Teléfono: {data['phone']}\n"
                f"Mensaje:\n{data['message']}\n"
            )
            sent_successfully = False
            error_message = ""
            try:
                print("=" * 80)
                print("[DEBUG] Iniciando proceso de envío de correo")

                email_config = EmailConfig.objects.first()

                if email_config:
                    print(f"[DEBUG] Configuración de correo encontrada:")
                    print(f"  - Host: {email_config.email_host}")
                    print(f"  - Puerto: {email_config.email_port}")
                    print(f"  - Usuario: {email_config.email_host_user}")
                    print(f"  - Contraseña: {'*' * len(email_config.email_host_password) if email_config.email_host_password else 'NO CONFIGURADA'}")
                    print(f"  - Use TLS: {email_config.email_use_tls}")
                    print(f"  - From Email: {email_config.default_from_email}")
                    print(f"  - Admin Email: {email_config.contact_admin_email}")

                    from django.core.mail import EmailMessage, get_connection

                    print("[DEBUG] Creando conexión SMTP...")
                    connection = get_connection(
                        backend='django.core.mail.backends.smtp.EmailBackend',
                        host=email_config.email_host,
                        port=email_config.email_port,
                        username=email_config.email_host_user,
                        password=email_config.email_host_password,
                        use_tls=email_config.email_use_tls,
                    )

                    # 1. Enviar mensaje del usuario al administrador
                    admin_email = email_config.contact_admin_email or email_config.email_host_user
                    print(f"[DEBUG] Preparando email al administrador: {admin_email}")

                    email_admin = EmailMessage(
                        subject,
                        body,
                        email_config.default_from_email or email_config.email_host_user,
                        [admin_email],
                        connection=connection
                    )

                    print("[DEBUG] Enviando email al administrador...")
                    email_admin.send(fail_silently=False)
                    print("[DEBUG] Email al administrador enviado exitosamente!")
                    # 2. Enviar mensaje de confirmación al usuario
                    confirm_subject = "RTV Pioli - Confirmación de contacto"
                    confirm_body = (
                        f"Estimado/a {data['name']},\n\n"
                        f"RTV Pioli recibió su mensaje. Le estaremos respondiendo a la brevedad.\n\n"
                        f"Gracias por contactarnos."
                    )

                    print(f"[DEBUG] Preparando email de confirmación al usuario: {data['email']}")
                    email_user = EmailMessage(
                        confirm_subject,
                        confirm_body,
                        email_config.default_from_email or email_config.email_host_user,
                        [data['email']],
                        connection=connection
                    )

                    print("[DEBUG] Enviando email de confirmación al usuario...")
                    email_user.send(fail_silently=False)
                    print("[DEBUG] Email de confirmación enviado exitosamente!")

                    sent_successfully = True
                    print("[DEBUG] ✓ Proceso completado exitosamente")
                    print("=" * 80)
                    messages.success(request, '¡Gracias por contactarnos! Tu mensaje fue enviado correctamente.')
                else:
                    error_message = 'No hay configuración de correo definida.'
                    print(f"[ERROR] {error_message}")
                    print("=" * 80)
            except Exception as e:
                error_message = str(e)
                print(f"[ERROR] Error al enviar correo: {error_message}")
                print(f"[ERROR] Tipo de error: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback completo:")
                traceback.print_exc()
                print("=" * 80)
                # Guardar el mensaje en el modelo si falla el envío
                
                ContactMessage.objects.create(
                    name=data['name'],
                    email=data['email'],
                    phone=data['phone'],
                    message=data['message'],
                    read=False,
                    replied=False,
                )
                messages.error(request, 'No se pudo enviar el mensaje por correo. Tu mensaje fue guardado y será revisado por el administrador.')
            return redirect('home')
        else:
            messages.error(request, 'Hubo un error en el formulario. Por favor verifica los datos.')

            # Volver a cargar la página con el formulario con errores
            site_config = SiteConfiguration.get_config()
            services = Service.objects.filter(active=True).order_by('order', 'title')
            portfolio_items = PortfolioItem.objects.filter(active=True).order_by('order', 'title')
            timeline_events = TimelineEvent.objects.filter(active=True).order_by('order', 'date')
            team_members = TeamMember.objects.filter(active=True).order_by('order', 'name')

            context = {
                'site_config': site_config,
                'services': services,
                'portfolio_items': portfolio_items,
                'timeline_events': timeline_events,
                'team_members': team_members,
                'form': form,
            }

            return render(request, 'home.html', context)
    else:
        # Si no es POST, redirigir a home
        return redirect('home')
