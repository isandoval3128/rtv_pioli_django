"""
Data migration:
1. Asignar orden a los grupos existentes para controlar el sidebar
2. Crear UserPermission 'Acceso Uso IA' y asignarlo al menú 'Uso IA / Costos'
3. Asignar ese permiso al usuario 20371056255
"""
from django.db import migrations


def set_orden_and_permission(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    GroupProfile = apps.get_model('panel_administracion', 'GroupProfile')
    UserPermission = apps.get_model('panel_administracion', 'UserPermission')
    MenuGrupo = apps.get_model('panel_administracion', 'MenuGrupo')
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('panel_administracion', 'UserProfile')

    # 1. Orden de grupos en el sidebar
    ordenes = {
        'Administración': 1,
        'Asistente IA': 2,
        'Turnos': 3,
    }
    for nombre, orden in ordenes.items():
        try:
            grupo = Group.objects.get(name=nombre)
            profile, _ = GroupProfile.objects.get_or_create(group=grupo)
            profile.orden = orden
            profile.save()
        except Group.DoesNotExist:
            pass

    # 2. Crear permiso para Uso IA / Costos
    permiso, _ = UserPermission.objects.get_or_create(
        nombre='Acceso Uso IA',
        defaults={'status': True}
    )

    # 3. Asignar permiso al menú "Uso IA / Costos"
    try:
        grupo_asistente = Group.objects.get(name='Asistente IA')
        menu_uso_ia = MenuGrupo.objects.filter(
            grupo=grupo_asistente,
            nombre='Uso IA / Costos'
        ).first()
        if menu_uso_ia:
            menu_uso_ia.userPermission = permiso
            menu_uso_ia.save()
    except Group.DoesNotExist:
        pass

    # 4. Asignar permiso al usuario 20371056255
    try:
        user = User.objects.get(username='20371056255')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.userPermission = permiso
        profile.save()
        # Asegurar que es staff
        if not user.is_staff:
            user.is_staff = True
            user.save()
    except User.DoesNotExist:
        pass


def reverse_migration(apps, schema_editor):
    UserPermission = apps.get_model('panel_administracion', 'UserPermission')
    MenuGrupo = apps.get_model('panel_administracion', 'MenuGrupo')
    Group = apps.get_model('auth', 'Group')

    # Quitar permiso del menú
    try:
        grupo = Group.objects.get(name='Asistente IA')
        MenuGrupo.objects.filter(
            grupo=grupo, nombre='Uso IA / Costos'
        ).update(userPermission=None)
    except Group.DoesNotExist:
        pass

    UserPermission.objects.filter(nombre='Acceso Uso IA').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('panel_administracion', '0009_groupprofile_orden'),
        ('asistente', '0002_crear_menu_asistente'),
    ]

    operations = [
        migrations.RunPython(set_orden_and_permission, reverse_migration),
    ]
