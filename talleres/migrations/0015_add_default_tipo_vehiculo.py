# Generated migration to add default TipoVehiculo
from django.db import migrations
from django.utils import timezone


def create_default_tipo_vehiculo(apps, schema_editor):
    """Crea un TipoVehiculo por defecto para turnos sin seleccion manual"""
    TipoVehiculo = apps.get_model('talleres', 'TipoVehiculo')

    # Verificar si ya existe
    if not TipoVehiculo.objects.filter(codigo_tramite='DEFAULT').exists():
        TipoVehiculo.objects.create(
            codigo_tramite='DEFAULT',
            nombre='Turno General',
            descripcion='Tipo de tramite por defecto para turnos sin seleccion especifica. Creado automaticamente por el sistema.',
            duracion_minutos=30,
            precio=0,
            precio_provincial=None,
            precio_nacional=None,
            precio_cajutad=None,
            status=True,
        )


def remove_default_tipo_vehiculo(apps, schema_editor):
    """Elimina el TipoVehiculo por defecto (para rollback)"""
    TipoVehiculo = apps.get_model('talleres', 'TipoVehiculo')
    TipoVehiculo.objects.filter(codigo_tramite='DEFAULT').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('talleres', '0014_alter_tipovehiculo_options'),
    ]

    operations = [
        migrations.RunPython(create_default_tipo_vehiculo, remove_default_tipo_vehiculo),
    ]
