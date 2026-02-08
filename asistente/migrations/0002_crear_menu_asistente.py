"""
Data migration para crear el grupo y menú del Asistente IA en el sidebar del panel.
"""
from django.db import migrations


def crear_menu_asistente(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    GroupProfile = apps.get_model('panel_administracion', 'GroupProfile')
    MenuGrupo = apps.get_model('panel_administracion', 'MenuGrupo')

    # Crear grupo "Asistente IA" si no existe
    grupo, created = Group.objects.get_or_create(name='Asistente IA')

    # Crear perfil del grupo con icono
    GroupProfile.objects.get_or_create(
        group=grupo,
        defaults={
            'icon': 'fa fa-robot',
            'home': '/panel/asistente/config/',
        }
    )

    # Crear entradas de menú
    menus = [
        {'nombre': 'Configuración', 'url': '/panel/asistente/config/', 'orden': 1},
        {'nombre': 'Preguntas Frecuentes', 'url': '/panel/asistente/faqs/', 'orden': 2},
        {'nombre': 'Conversaciones', 'url': '/panel/asistente/conversaciones/', 'orden': 3},
        {'nombre': 'Uso IA / Costos', 'url': '/panel/asistente/uso-ia/', 'orden': 4},
    ]

    for menu_data in menus:
        MenuGrupo.objects.get_or_create(
            grupo=grupo,
            nombre=menu_data['nombre'],
            defaults={
                'url': menu_data['url'],
                'orden': menu_data['orden'],
                'status': True,
            }
        )


def eliminar_menu_asistente(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    MenuGrupo = apps.get_model('panel_administracion', 'MenuGrupo')

    try:
        grupo = Group.objects.get(name='Asistente IA')
        MenuGrupo.objects.filter(grupo=grupo).delete()
        grupo.delete()
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('asistente', '0001_initial'),
        ('panel_administracion', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(crear_menu_asistente, eliminar_menu_asistente),
    ]
