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
            {'name': 'Asistente IA'},
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
                'orden': 1,
            },
            {
                'grupo_name': 'Asistente IA',
                'icon': 'icon-bubbles',
                'home': '/panel/asistente/config/',
                'orden': 2,
            },
            {
                'grupo_name': 'Turnos',
                'icon': 'icon-calendar',
                'home': '/panel/turnos/',
                'orden': 3,
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
                    profile.orden = perfil_data.get('orden', 0)
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
            # --- Administración ---
            {'grupo_name': 'Administración', 'nombre': 'Gestión Usuarios', 'url': '/panel/usuarios/', 'orden': 1, 'status': True},
            {'grupo_name': 'Administración', 'nombre': 'Gestión Sitio', 'url': '/panel/sitio/', 'orden': 2, 'status': True},
            # --- Asistente IA ---
            {'grupo_name': 'Asistente IA', 'nombre': 'Dashboard', 'url': '/panel/asistente/dashboard/', 'orden': 1, 'status': True},
            {'grupo_name': 'Asistente IA', 'nombre': 'Preguntas Frecuentes', 'url': '/panel/asistente/faqs/', 'orden': 2, 'status': True},
            {'grupo_name': 'Asistente IA', 'nombre': 'Base de Conocimiento', 'url': '/panel/asistente/kb/', 'orden': 3, 'status': True},
            {'grupo_name': 'Asistente IA', 'nombre': 'Conversaciones', 'url': '/panel/asistente/conversaciones/', 'orden': 4, 'status': True},
            {'grupo_name': 'Asistente IA', 'nombre': 'Sugerencias', 'url': '/panel/asistente/sugerencias/', 'orden': 5, 'status': True},
            {'grupo_name': 'Asistente IA', 'nombre': 'Uso IA / Costos', 'url': '/panel/asistente/uso-ia/', 'orden': 6, 'status': True},
            {'grupo_name': 'Asistente IA', 'nombre': 'Configuración', 'url': '/panel/asistente/config/', 'orden': 7, 'status': True},
            # --- Turnos ---
            {'grupo_name': 'Turnos', 'nombre': 'Dashboard', 'url': '/panel/turnos/dashboard/', 'orden': 1, 'status': True},
            {'grupo_name': 'Turnos', 'nombre': 'Gestión Turnos', 'url': '/panel/turnos/', 'orden': 2, 'status': True},
            {'grupo_name': 'Turnos', 'nombre': 'Escanear Turno', 'url': '/panel/turnos/escanear/', 'orden': 3, 'status': True},
            {'grupo_name': 'Turnos', 'nombre': 'Configuraciones', 'url': '/panel/parametros/', 'orden': 4, 'status': True},
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
