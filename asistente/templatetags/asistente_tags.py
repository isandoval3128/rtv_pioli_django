from django import template
from asistente.models import AsistenteConfigModel

register = template.Library()


@register.inclusion_tag('asistente/chat_widget.html', takes_context=True)
def chat_widget(context):
    config = AsistenteConfigModel.get_config()
    return {
        'asistente_config': config,
        'asistente_habilitado': config.habilitado,
        'nombre_asistente': config.nombre_asistente,
        'auto_open_delay': config.auto_open_delay,
    }
