from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Service, PortfolioItem, TimelineEvent, TeamMember, SiteConfiguration
from .forms import ContactForm


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

    context = {
        'site_config': site_config,
        'services': services,
        'portfolio_items': portfolio_items,
        'timeline_events': timeline_events,
        'team_members': team_members,
        'form': form,
    }

    return render(request, 'home.html', context)


def contact_submit(request):
    """
    Vista para procesar el formulario de contacto
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            # Guardar el mensaje
            form.save()
            messages.success(request, '¡Gracias por contactarnos!')
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
