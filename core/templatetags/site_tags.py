from django import template
from core.models import SiteConfiguration

register = template.Library()


@register.filter
def sort_by_orden(groups):
    """Ordena grupos por el campo 'orden' de su GroupProfile"""
    return sorted(
        groups,
        key=lambda g: getattr(getattr(g, 'panel_profile', None), 'orden', 999)
    )


@register.simple_tag
def get_site_config():
    """
    Template tag para obtener la configuración del sitio
    Uso: {% get_site_config as site_config %}
    """
    return SiteConfiguration.get_config()


@register.inclusion_tag('includes/dynamic_css.html')
def dynamic_css():
    """
    Template tag para inyectar CSS dinámico desde SiteConfiguration
    Uso: {% dynamic_css %}
    """
    config = SiteConfiguration.get_config()
    return {'config': config}
