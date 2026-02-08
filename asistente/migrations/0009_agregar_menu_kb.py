"""
Data migration para agregar 'Base de Conocimiento' al menú del Asistente IA.
"""
from django.db import migrations


def agregar_menu_kb(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    MenuGrupo = apps.get_model('panel_administracion', 'MenuGrupo')

    try:
        grupo = Group.objects.get(name='Asistente IA')
    except Group.DoesNotExist:
        return

    MenuGrupo.objects.get_or_create(
        grupo=grupo,
        nombre='Base de Conocimiento',
        defaults={
            'url': '/panel/asistente/kb/',
            'orden': 3,  # Después de FAQs (2), antes de Conversaciones
            'status': True,
        }
    )

    # Reordenar los que vienen después para evitar colisión
    MenuGrupo.objects.filter(
        grupo=grupo, nombre='Conversaciones'
    ).update(orden=4)
    MenuGrupo.objects.filter(
        grupo=grupo, nombre='Uso IA / Costos'
    ).update(orden=5)


def eliminar_menu_kb(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    MenuGrupo = apps.get_model('panel_administracion', 'MenuGrupo')

    try:
        grupo = Group.objects.get(name='Asistente IA')
        MenuGrupo.objects.filter(grupo=grupo, nombre='Base de Conocimiento').delete()
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('asistente', '0008_alter_chatmessage_source'),
        ('panel_administracion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(agregar_menu_kb, eliminar_menu_kb),
    ]
