from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Service, PortfolioItem, TimelineEvent, TeamMember, SiteConfiguration
from .forms import ContactForm
import json
from .models import AboutSection
from tarifas.models import Tarifa
from tarifas.utils import excel_to_html

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

    # Crear form de contacto vacío
    form = ContactForm()

    # Obtener ubicaciones dinámicas
    try:
        from ubicacion.models import Ubicacion
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
            from django.conf import settings
            from django.core.mail import send_mail, BadHeaderError
            subject = f"Nuevo mensaje RTV Pioli web de {data['name']}"
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
                from .models import EmailConfig
                email_config = EmailConfig.objects.first()
                if email_config:
                    from django.core.mail import EmailMessage, get_connection
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
                    email_admin = EmailMessage(
                        subject,
                        body,
                        email_config.default_from_email or email_config.email_host_user,
                        [admin_email],
                        connection=connection
                    )
                    email_admin.send(fail_silently=False)
                    # 2. Enviar mensaje de confirmación al usuario
                    confirm_subject = "RTV Pioli - Confirmación de contacto"
                    confirm_body = (
                        f"Estimado/a {data['name']},\n\n"
                        f"RTV Pioli recibió su mensaje. Le estaremos respondiendo a la brevedad.\n\n"
                        f"Gracias por contactarnos."
                    )
                    email_user = EmailMessage(
                        confirm_subject,
                        confirm_body,
                        email_config.default_from_email or email_config.email_host_user,
                        [data['email']],
                        connection=connection
                    )
                    email_user.send(fail_silently=False)
                    sent_successfully = True
                    messages.success(request, '¡Gracias por contactarnos! Tu mensaje fue enviado correctamente.')
                else:
                    error_message = 'No hay configuración de correo definida.'
            except Exception as e:
                error_message = str(e)
                # Guardar el mensaje en el modelo si falla el envío
                from .models import ContactMessage
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
