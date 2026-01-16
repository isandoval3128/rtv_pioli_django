"""
Comando para inicializar los datos del menú del panel en producción.
Crea los grupos, perfiles de grupo y menús necesarios para el funcionamiento del panel.

Uso: python manage.py inicializar_menu_produccion
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from panel_administracion.models import GroupProfile, MenuGrupo, Sector, UserPermission


class Command(BaseCommand):
    help = 'Inicializa los grupos, perfiles y menús del panel de administración'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de datos existentes',
        )

    def handle(self, *args, **options):
        force = options['force']

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('  INICIALIZACIÓN DE MENÚ - RTV PIOLI'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write('')

        # =====================================================
        # 1. CREAR GRUPOS
        # =====================================================
        self.stdout.write(self.style.NOTICE('Paso 1: Creando grupos...'))

        grupos_config = [
            {'name': 'Administración'},
            {'name': 'Turnos'},
        ]

        grupos_creados = {}
        for grupo_data in grupos_config:
            grupo, created = Group.objects.get_or_create(name=grupo_data['name'])
            grupos_creados[grupo_data['name']] = grupo
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Grupo "{grupo.name}" creado'))
            else:
                self.stdout.write(f'  - Grupo "{grupo.name}" ya existe')

        self.stdout.write('')

        # =====================================================
        # 2. CREAR/ACTUALIZAR PERFILES DE GRUPO
        # =====================================================
        self.stdout.write(self.style.NOTICE('Paso 2: Configurando perfiles de grupo...'))

        perfiles_config = [
            {
                'grupo_name': 'Administración',
                'icon': 'icon-settings',
                'home': '/panel/',
            },
            {
                'grupo_name': 'Turnos',
                'icon': 'icon-calendar',
                'home': '/panel/turnos/',
            },
        ]

        for perfil_data in perfiles_config:
            grupo = grupos_creados.get(perfil_data['grupo_name'])
            if grupo:
                profile, created = GroupProfile.objects.get_or_create(group=grupo)

                # Actualizar datos si es forzado o si es nuevo
                if created or force:
                    profile.icon = perfil_data['icon']
                    profile.home = perfil_data['home']
                    profile.save()

                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ Perfil para "{grupo.name}" creado (icon: {profile.icon}, home: {profile.home})'
                        ))
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ Perfil para "{grupo.name}" actualizado'
                        ))
                else:
                    self.stdout.write(f'  - Perfil para "{grupo.name}" ya existe (use --force para actualizar)')

        self.stdout.write('')

        # =====================================================
        # 3. CREAR MENÚS
        # =====================================================
        self.stdout.write(self.style.NOTICE('Paso 3: Creando menús...'))

        menus_config = [
            # Menús para grupo "Turnos"
            {
                'grupo_name': 'Turnos',
                'nombre': 'Gestión Turnos',
                'url': '/panel/turnos/',
                'orden': 1,
                'status': True,
            },
            # Menús para grupo "Administración" (agregar más según necesidad)
            # {
            #     'grupo_name': 'Administración',
            #     'nombre': 'Dashboard',
            #     'url': '/panel/',
            #     'orden': 1,
            #     'status': True,
            # },
        ]

        for menu_data in menus_config:
            grupo = grupos_creados.get(menu_data['grupo_name'])
            if grupo:
                # Buscar si existe un menú con el mismo nombre y grupo
                menu_existente = MenuGrupo.objects.filter(
                    grupo=grupo,
                    nombre=menu_data['nombre']
                ).first()

                if menu_existente:
                    if force:
                        menu_existente.url = menu_data['url']
                        menu_existente.orden = menu_data['orden']
                        menu_existente.status = menu_data['status']
                        menu_existente.save()
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ Menú "{menu_data["nombre"]}" ({grupo.name}) actualizado'
                        ))
                    else:
                        self.stdout.write(
                            f'  - Menú "{menu_data["nombre"]}" ({grupo.name}) ya existe'
                        )
                else:
                    MenuGrupo.objects.create(
                        grupo=grupo,
                        nombre=menu_data['nombre'],
                        url=menu_data['url'],
                        orden=menu_data['orden'],
                        status=menu_data['status'],
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Menú "{menu_data["nombre"]}" ({grupo.name}) creado'
                    ))

        self.stdout.write('')

        # =====================================================
        # RESUMEN
        # =====================================================
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.SUCCESS('  INICIALIZACIÓN COMPLETADA'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write('')
        self.stdout.write('Resumen:')
        self.stdout.write(f'  - Grupos: {Group.objects.count()}')
        self.stdout.write(f'  - Perfiles de Grupo: {GroupProfile.objects.count()}')
        self.stdout.write(f'  - Menús: {MenuGrupo.objects.count()}')
        self.stdout.write('')
        self.stdout.write('Para agregar usuarios a los grupos, usa el Django Admin:')
        self.stdout.write('  /admin/auth/user/')
        self.stdout.write('')
