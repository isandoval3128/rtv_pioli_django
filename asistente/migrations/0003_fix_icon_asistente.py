"""
Data migration para corregir el icono del grupo Asistente IA.
El panel usa Simple Line Icons (icon-*), no Font Awesome 5+ (fa fa-robot).
"""
from django.db import migrations


def fix_icon(apps, schema_editor):
    GroupProfile = apps.get_model('panel_administracion', 'GroupProfile')
    Group = apps.get_model('auth', 'Group')

    try:
        grupo = Group.objects.get(name='Asistente IA')
        profile = GroupProfile.objects.get(group=grupo)
        profile.icon = 'icon-bubbles'
        profile.save()
    except (Group.DoesNotExist, GroupProfile.DoesNotExist):
        pass


def revert_icon(apps, schema_editor):
    GroupProfile = apps.get_model('panel_administracion', 'GroupProfile')
    Group = apps.get_model('auth', 'Group')

    try:
        grupo = Group.objects.get(name='Asistente IA')
        profile = GroupProfile.objects.get(group=grupo)
        profile.icon = 'fa fa-robot'
        profile.save()
    except (Group.DoesNotExist, GroupProfile.DoesNotExist):
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('asistente', '0002_crear_menu_asistente'),
    ]

    operations = [
        migrations.RunPython(fix_icon, revert_icon),
    ]
