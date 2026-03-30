from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from datetime import time, date, timedelta, datetime
from .models import UserPermission, MenuGrupo, Sector, UserProfile, GroupProfile


# Inline para UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil del Panel'
    fk_name = 'user'


# Desregistrar el admin por defecto de User
admin.site.unregister(User)


class CustomUserAdmin(UserAdmin):
    """Admin personalizado para User con perfil del panel"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_sector', 'get_permission')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    change_list_template = 'admin/auth/user_change_list.html'

    def get_sector(self, obj):
        try:
            if hasattr(obj, 'panel_profile') and obj.panel_profile and obj.panel_profile.sector:
                return obj.panel_profile.sector.nombre
        except UserProfile.DoesNotExist:
            pass
        return '-'
    get_sector.short_description = 'Sector'

    def get_permission(self, obj):
        try:
            if hasattr(obj, 'panel_profile') and obj.panel_profile and obj.panel_profile.userPermission:
                return obj.panel_profile.userPermission.nombre
        except UserProfile.DoesNotExist:
            pass
        return '-'
    get_permission.short_description = 'Permiso'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        # Asegurar que existe el perfil
        UserProfile.objects.get_or_create(user=obj)
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'iniciar-sistema/',
                self.admin_site.admin_view(self.iniciar_sistema_view),
                name='panel_administracion_iniciar_sistema'
            ),
        ]
        return custom_urls + urls

    def iniciar_sistema_view(self, request):
        """Vista para iniciar el sistema (producción o prueba)."""
        if request.method == 'POST':
            modo = request.POST.get('modo')
            if modo == 'produccion':
                resultado = self._iniciar_produccion()
            elif modo == 'prueba':
                resultado = self._iniciar_prueba()
            else:
                messages.error(request, 'Modo no válido.')
                return render(request, 'admin/panel_administracion/iniciar_sistema.html',
                              {**self.admin_site.each_context(request), 'title': 'Iniciar Sistema'})

            messages.success(request, resultado['titulo'])
            context = {
                **self.admin_site.each_context(request),
                'title': 'Iniciar Sistema',
                'resultado': resultado,
            }
            return render(request, 'admin/panel_administracion/iniciar_sistema.html', context)

        # GET
        context = {
            **self.admin_site.each_context(request),
            'title': 'Iniciar Sistema',
        }
        return render(request, 'admin/panel_administracion/iniciar_sistema.html', context)

    def _limpiar_base_datos(self):
        """Limpia datos transaccionales del sistema.
        PROTEGE (no se toca):
          - Usuarios, perfiles, grupos, permisos, sectores (se crean/actualizan sin borrar)
          - Talleres, TipoVehiculo, ConfiguracionTaller, FranjaAnulada
          - EmailConfig, SiteConfiguration, WhatsAppConfig
          - AsistenteConfigModel, FAQ, DocumentoKB
          - Tarifa, Territorios, Ubicacion
          - Contenido del sitio (Service, Portfolio, Timeline, Team, About)
        LIMPIA:
          - Turnos, historial, reservas temporales
          - Clientes, vehiculos
          - Chats, cache, derivaciones, sugerencias, logs IA del asistente
          - Sesiones de Django
        """
        from turnero.models import Turno, HistorialTurno, ReservaTemporal
        from talleres.models import Vehiculo
        from clientes.models import Cliente
        from asistente.models import ChatSession, ChatMessage, CachedResponse, Derivacion
        from asistente.models import SugerenciaAsistente, SugerenciaToken, AIUsageLog

        mensajes = []

        # Limpiar datos transaccionales del asistente (mantener config, FAQs y KB)
        count = ChatMessage.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} mensajes de chat del asistente')
        count = ChatSession.objects.all().delete()[0]
        mensajes.append(f'Eliminadas {count} sesiones de chat del asistente')
        count = CachedResponse.objects.all().delete()[0]
        mensajes.append(f'Eliminadas {count} respuestas cacheadas del asistente')
        count = Derivacion.objects.all().delete()[0]
        mensajes.append(f'Eliminadas {count} derivaciones del asistente')
        count = SugerenciaToken.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} tokens de sugerencias')
        count = SugerenciaAsistente.objects.all().delete()[0]
        mensajes.append(f'Eliminadas {count} sugerencias del asistente')
        count = AIUsageLog.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} registros de uso IA')

        # Eliminar turnos y relacionados
        count = HistorialTurno.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} registros de historial de turnos')
        count = ReservaTemporal.objects.all().delete()[0]
        mensajes.append(f'Eliminadas {count} reservas temporales')
        count = Turno.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} turnos')

        # Eliminar vehiculos y clientes (NO talleres, tipos ni configuraciones)
        count = Vehiculo.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} vehiculos')
        count = Cliente.objects.all().delete()[0]
        mensajes.append(f'Eliminados {count} clientes')

        # NO se eliminan: usuarios, perfiles, grupos, menús, sectores, permisos
        mensajes.append('Usuarios y configuracion de acceso preservados')

        # Limpiar sesiones de Django
        from django.contrib.sessions.models import Session
        count = Session.objects.all().delete()[0]
        mensajes.append(f'Eliminadas {count} sesiones')

        return mensajes

    def _crear_sectores(self):
        """Crea los sectores del sistema."""
        mensajes = []
        sector_admin, created = Sector.objects.get_or_create(
            codigo=Sector.SECTOR_ADMINISTRACION,
            defaults={'nombre': 'Administracion', 'status': True}
        )
        mensajes.append(f'Sector Administracion {"creado" if created else "ya existe"}')

        sector_taller, created = Sector.objects.get_or_create(
            codigo=Sector.SECTOR_TALLER,
            defaults={'nombre': 'Taller', 'status': True}
        )
        mensajes.append(f'Sector Taller {"creado" if created else "ya existe"}')

        return sector_admin, sector_taller, mensajes

    def _crear_superusuarios(self, sector_admin):
        """Crea los 2 superusuarios del sistema con permiso Administrador."""
        mensajes = []

        # Crear permiso Administrador
        perm_admin, _ = UserPermission.objects.get_or_create(
            nombre=MenuGrupoAdmin.PERMISO_ADMINISTRADOR,
            defaults={'status': True}
        )

        # Usuario 20371056255
        user1, created = User.objects.get_or_create(
            username='20371056255',
            defaults={
                'first_name': 'Ivan',
                'last_name': 'Sandoval',
                'email': 'ivansandval3128@gmail.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            user1.set_password('Pastillas992$')
            user1.save()
        mensajes.append(f'Usuario 20371056255 {"creado" if created else "ya existe"} (superusuario, sector=Administracion, rol=Gerente, permiso=Administrador)')

        # Usuario admin
        user2, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Admin',
                'last_name': 'Pioli',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            user2.set_password('Pioli2026$')
            user2.save()
        mensajes.append(f'Usuario admin {"creado" if created else "ya existe"} (superusuario, sector=Administracion, rol=Gerente, permiso=Administrador)')

        # Asegurar perfiles completos
        for user in [user1, user2]:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.sector = sector_admin
            profile.origen = 'GERENTE'
            profile.userPermission = perm_admin
            profile.save()

        return user1, user2, mensajes

    def _sincronizar_menus_y_asignar(self, usuarios):
        """Sincroniza menús desde MENU_CONFIG y asigna todos los grupos a los usuarios."""
        mensajes = []

        for grupo_cfg in MenuGrupoAdmin.MENU_CONFIG:
            # Crear grupo
            grupo, created = Group.objects.get_or_create(name=grupo_cfg['grupo_name'])
            if created:
                mensajes.append(f'Grupo "{grupo.name}" creado')

            # Crear perfil de grupo
            profile, _ = GroupProfile.objects.get_or_create(group=grupo)
            profile.icon = grupo_cfg['icon']
            profile.home = grupo_cfg['home']
            profile.orden = grupo_cfg['orden']
            profile.save()

            # Crear menús
            for menu_cfg in grupo_cfg['menus']:
                permission = None
                if menu_cfg.get('permission'):
                    permission, _ = UserPermission.objects.get_or_create(
                        nombre=menu_cfg['permission'],
                        defaults={'status': True}
                    )

                MenuGrupo.objects.get_or_create(
                    grupo=grupo,
                    nombre=menu_cfg['nombre'],
                    defaults={
                        'url': menu_cfg['url'],
                        'orden': menu_cfg['orden'],
                        'userPermission': permission,
                        'status': True,
                    }
                )
                mensajes.append(f'Menu "{menu_cfg["nombre"]}" creado en {grupo.name}')

            # Asignar grupo a todos los usuarios indicados
            for user in usuarios:
                user.groups.add(grupo)

        # Asignar TODOS los submenús a los usuarios indicados (superusuarios)
        todos_menus = MenuGrupo.objects.filter(status=True)
        for user in usuarios:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.menus_permitidos.add(*todos_menus)

        mensajes.append(f'Todos los grupos y submenus asignados a {len(usuarios)} usuarios')
        return mensajes

    def _iniciar_produccion(self):
        """Inicializa el sistema para producción."""
        secciones = []

        # 1. Limpiar BD
        msgs = self._limpiar_base_datos()
        secciones.append({'titulo': 'Limpieza de Base de Datos', 'mensajes': msgs})

        # 2. Crear sectores
        sector_admin, sector_taller, msgs = self._crear_sectores()
        secciones.append({'titulo': 'Sectores', 'mensajes': msgs})

        # 3. Crear superusuarios
        user1, user2, msgs = self._crear_superusuarios(sector_admin)
        secciones.append({'titulo': 'Superusuarios', 'mensajes': msgs})

        # 4. Sincronizar menús y asignar
        msgs = self._sincronizar_menus_y_asignar([user1, user2])
        secciones.append({'titulo': 'Menus y Grupos', 'mensajes': msgs})

        return {
            'titulo': 'Sistema iniciado para PRODUCCION correctamente',
            'secciones': secciones,
        }

    def _iniciar_prueba(self):
        """Inicializa el sistema con datos de prueba."""
        from turnero.models import Turno, HistorialTurno
        from talleres.models import Taller, TipoVehiculo, ConfiguracionTaller, Vehiculo
        from clientes.models import Cliente

        secciones = []

        # 1. Limpiar BD
        msgs = self._limpiar_base_datos()
        secciones.append({'titulo': 'Limpieza de Base de Datos', 'mensajes': msgs})

        # 2. Crear sectores
        sector_admin, sector_taller, msgs = self._crear_sectores()
        secciones.append({'titulo': 'Sectores', 'mensajes': msgs})

        # 3. Crear superusuarios
        user1, user2, msgs = self._crear_superusuarios(sector_admin)
        secciones.append({'titulo': 'Superusuarios', 'mensajes': msgs})

        # 4. Crear usuarios de prueba
        msgs_test = []

        # Usuario administración
        user_admin_test, created = User.objects.get_or_create(
            username='operador_admin',
            defaults={
                'first_name': 'Maria',
                'last_name': 'Lopez',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if created:
            user_admin_test.set_password('Test1234$')
            user_admin_test.save()
        profile_admin, _ = UserProfile.objects.get_or_create(user=user_admin_test)
        profile_admin.sector = sector_admin
        profile_admin.origen = 'ADMINISTRATIVO'
        profile_admin.save()
        msgs_test.append('Usuario operador_admin creado (Sector: Administracion, Rol: Administrativo)')

        # Usuario taller
        user_taller_test, created = User.objects.get_or_create(
            username='operador_taller',
            defaults={
                'first_name': 'Juan',
                'last_name': 'Garcia',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if created:
            user_taller_test.set_password('Test1234$')
            user_taller_test.save()
        profile_taller, _ = UserProfile.objects.get_or_create(user=user_taller_test)
        profile_taller.sector = sector_taller
        profile_taller.origen = 'OPERARIO_AUTO'
        profile_taller.save()
        msgs_test.append('Usuario operador_taller creado (Sector: Taller, Rol: Operario Auto)')

        secciones.append({'titulo': 'Usuarios de Prueba', 'mensajes': msgs_test})

        # 5. Sincronizar menús
        todos_los_usuarios = [user1, user2, user_admin_test, user_taller_test]
        msgs = self._sincronizar_menus_y_asignar([user1, user2])
        secciones.append({'titulo': 'Menus y Grupos (Superusuarios)', 'mensajes': msgs})

        # 6. Asignar menús específicos a usuarios de prueba
        msgs_permisos = []

        grupo_inicio = Group.objects.get(name='Inicio')
        grupo_turnos = Group.objects.get(name='Turnos')

        # Submenús de Inicio para operadores (solo Dashboard Turnos)
        menu_dashboard_turnos = MenuGrupo.objects.filter(
            grupo=grupo_inicio,
            nombre='Dashboard Turnos',
            status=True
        )

        # Submenús de Turnos para operadores (Gestión Turnos y Escanear Turno)
        menus_turnos_operador = MenuGrupo.objects.filter(
            grupo=grupo_turnos,
            nombre__in=['Gestión Turnos', 'Escanear Turno'],
            status=True
        )

        for user_test, profile_test, label in [
            (user_admin_test, profile_admin, 'operador_admin'),
            (user_taller_test, profile_taller, 'operador_taller'),
        ]:
            user_test.groups.add(grupo_inicio, grupo_turnos)
            profile_test.menus_permitidos.add(*menu_dashboard_turnos, *menus_turnos_operador)
            menus_names = ', '.join(m.nombre for m in list(menu_dashboard_turnos) + list(menus_turnos_operador))
            msgs_permisos.append(f'{label}: grupos [Inicio, Turnos] con submenus [{menus_names}]')

        secciones.append({'titulo': 'Permisos de Usuarios de Prueba', 'mensajes': msgs_permisos})

        # 7. Usar talleres y tipos existentes (NO se borran)
        msgs_datos = []

        talleres = list(Taller.objects.filter(status=True))
        tipos = list(TipoVehiculo.objects.filter(status=True))
        configs = ConfiguracionTaller.objects.filter(status=True).count()

        if not talleres or not tipos:
            msgs_datos.append('ERROR: No hay talleres o tipos de tramite configurados. Crearlos antes de iniciar con datos de prueba.')
            secciones.append({'titulo': 'Talleres y Tipos de Tramite', 'mensajes': msgs_datos})
            return {
                'titulo': 'ERROR: Faltan datos necesarios para el turnero',
                'secciones': secciones,
            }

        for t in talleres:
            msgs_datos.append(f'Taller existente: {t.nombre} (id={t.id})')
        for tv in tipos:
            msgs_datos.append(f'Tipo tramite existente: {tv} (id={tv.id})')
        msgs_datos.append(f'Configuraciones de taller existentes: {configs}')

        taller1 = talleres[0]
        taller2 = talleres[1] if len(talleres) > 1 else talleres[0]
        tipo_auto = tipos[0]
        tipo_camion = tipos[1] if len(tipos) > 1 else tipos[0]

        secciones.append({'titulo': 'Talleres y Tipos de Tramite (existentes, no se tocan)', 'mensajes': msgs_datos})

        # 8. Crear clientes y vehiculos
        msgs_clientes = []

        clientes_data = [
            {'nombre': 'Carlos', 'apellido': 'Martinez', 'dni': '30123456', 'email': 'carlos@test.com', 'celular': '3884111111'},
            {'nombre': 'Ana', 'apellido': 'Rodriguez', 'dni': '28654321', 'email': 'ana@test.com', 'celular': '3884222222'},
            {'nombre': 'Roberto', 'apellido': 'Fernandez', 'dni': '35789012', 'email': 'roberto@test.com', 'celular': '3884333333'},
            {'nombre': 'Laura', 'apellido': 'Gomez', 'dni': '32456789', 'email': 'laura@test.com', 'celular': '3884444444'},
            {'nombre': 'Diego', 'apellido': 'Sanchez', 'dni': '29876543', 'email': 'diego@test.com', 'celular': '3884555555'},
        ]

        clientes = []
        for cd in clientes_data:
            cliente = Cliente.objects.create(**cd)
            clientes.append(cliente)
            msgs_clientes.append(f'Cliente creado: {cliente.nombre_completo}')

        vehiculos_data = [
            {'dominio': 'ABC123', 'marca': 'Ford', 'modelo': 'Focus', 'cliente': clientes[0], 'tipo_vehiculo': tipo_auto},
            {'dominio': 'DEF456', 'marca': 'Chevrolet', 'modelo': 'Corsa', 'cliente': clientes[1], 'tipo_vehiculo': tipo_auto},
            {'dominio': 'GHI789', 'marca': 'Fiat', 'modelo': 'Palio', 'cliente': clientes[2], 'tipo_vehiculo': tipo_auto},
            {'dominio': 'AB123CD', 'marca': 'Toyota', 'modelo': 'Hilux', 'cliente': clientes[3], 'tipo_vehiculo': tipo_auto},
            {'dominio': 'JK456LM', 'marca': 'Scania', 'modelo': 'R450', 'cliente': clientes[4], 'tipo_vehiculo': tipo_camion},
        ]

        vehiculos = []
        for vd in vehiculos_data:
            vehiculo = Vehiculo.objects.create(**vd)
            vehiculos.append(vehiculo)
            msgs_clientes.append(f'Vehiculo creado: {vehiculo.dominio} ({vehiculo.marca} {vehiculo.modelo})')

        secciones.append({'titulo': 'Clientes y Vehiculos', 'mensajes': msgs_clientes})

        # 9. Crear turnos con circuito completo
        msgs_turnos = []

        # Calcular fechas relativas
        # Buscar próximo día laboral (lun-vie)
        def proximo_dia_laboral(desde, dias_adelante=0):
            d = desde + timedelta(days=dias_adelante)
            while d.weekday() >= 5:  # sab=5, dom=6
                d += timedelta(days=1)
            return d

        hoy = date.today()
        manana = proximo_dia_laboral(hoy, 1)
        pasado = proximo_dia_laboral(hoy, 2)
        en_3_dias = proximo_dia_laboral(hoy, 3)
        ayer = hoy - timedelta(days=1)

        # Turno 1: PENDIENTE para mañana (recién creado, sin atender)
        turno1 = Turno(
            vehiculo=vehiculos[0],
            cliente=clientes[0],
            taller=taller1,
            tipo_vehiculo=tipo_auto,
            fecha=manana,
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
            estado='PENDIENTE',
            created_by=user1,
        )
        turno1.save()
        HistorialTurno.objects.create(
            turno=turno1, accion='CREACION',
            descripcion=f'Turno creado para {clientes[0].nombre_completo}',
            usuario=user1,
        )
        msgs_turnos.append(f'Turno {turno1.codigo} - PENDIENTE para {manana} 09:00 (Ford Focus ABC123)')

        # Turno 2: PENDIENTE para pasado mañana
        turno2 = Turno(
            vehiculo=vehiculos[1],
            cliente=clientes[1],
            taller=taller1,
            tipo_vehiculo=tipo_auto,
            fecha=pasado,
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            estado='PENDIENTE',
            created_by=user1,
        )
        turno2.save()
        HistorialTurno.objects.create(
            turno=turno2, accion='CREACION',
            descripcion=f'Turno creado para {clientes[1].nombre_completo}',
            usuario=user1,
        )
        msgs_turnos.append(f'Turno {turno2.codigo} - PENDIENTE para {pasado} 10:00 (Chevrolet Corsa DEF456)')

        # Turno 3: CONFIRMADO para hoy (fue escaneado por operador_taller)
        turno3 = Turno(
            vehiculo=vehiculos[2],
            cliente=clientes[2],
            taller=taller1,
            tipo_vehiculo=tipo_auto,
            fecha=hoy,
            hora_inicio=time(8, 30),
            hora_fin=time(9, 0),
            estado='CONFIRMADO',
            created_by=user1,
            atendido_por=user_taller_test,
            fecha_atencion=timezone.now().replace(hour=8, minute=35),
        )
        turno3.save()
        HistorialTurno.objects.create(
            turno=turno3, accion='CREACION',
            descripcion=f'Turno creado para {clientes[2].nombre_completo}',
            usuario=user1,
        )
        HistorialTurno.objects.create(
            turno=turno3, accion='ATENCION_REGISTRADA',
            descripcion=f'Turno confirmado por {user_taller_test.get_full_name()}',
            usuario=user_taller_test,
        )
        msgs_turnos.append(f'Turno {turno3.codigo} - CONFIRMADO hoy 08:30 (atendido por operador_taller - Fiat Palio GHI789)')

        # Turno 4: PENDIENTE para hoy (aún no fue escaneado, esperando atención)
        turno4 = Turno(
            vehiculo=vehiculos[3],
            cliente=clientes[3],
            taller=taller1,
            tipo_vehiculo=tipo_auto,
            fecha=hoy,
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
            estado='PENDIENTE',
            created_by=user1,
        )
        turno4.save()
        HistorialTurno.objects.create(
            turno=turno4, accion='CREACION',
            descripcion=f'Turno creado para {clientes[3].nombre_completo}',
            usuario=user1,
        )
        msgs_turnos.append(f'Turno {turno4.codigo} - PENDIENTE hoy 11:00 (esperando atencion - Toyota Hilux AB123CD)')

        # Turno 5: CANCELADO
        turno5 = Turno(
            vehiculo=vehiculos[0],
            cliente=clientes[0],
            taller=taller2,
            tipo_vehiculo=tipo_auto,
            fecha=en_3_dias,
            hora_inicio=time(14, 0),
            hora_fin=time(14, 30),
            estado='CANCELADO',
            created_by=user1,
        )
        turno5.save()
        HistorialTurno.objects.create(
            turno=turno5, accion='CREACION',
            descripcion=f'Turno creado para {clientes[0].nombre_completo}',
            usuario=user1,
        )
        HistorialTurno.objects.create(
            turno=turno5, accion='Cancelacion',
            descripcion=f'Turno cancelado por el cliente',
            usuario=None,
        )
        msgs_turnos.append(f'Turno {turno5.codigo} - CANCELADO para {en_3_dias} 14:00 (Ford Focus ABC123)')

        # Turno 6: PENDIENTE en taller 2 (camión)
        turno6 = Turno(
            vehiculo=vehiculos[4],
            cliente=clientes[4],
            taller=taller2,
            tipo_vehiculo=tipo_camion,
            fecha=manana,
            hora_inicio=time(9, 0),
            hora_fin=time(9, 45),
            estado='PENDIENTE',
            created_by=user2,
        )
        turno6.save()
        HistorialTurno.objects.create(
            turno=turno6, accion='CREACION',
            descripcion=f'Turno creado para {clientes[4].nombre_completo}',
            usuario=user2,
        )
        msgs_turnos.append(f'Turno {turno6.codigo} - PENDIENTE para {manana} 09:00 en Palpala (Scania R450 JK456LM)')

        # Turno 7: CONFIRMADO ayer (circuito completo: creado -> escaneado por taller -> confirmado)
        turno7 = Turno(
            vehiculo=vehiculos[1],
            cliente=clientes[1],
            taller=taller1,
            tipo_vehiculo=tipo_auto,
            fecha=ayer,
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
            estado='CONFIRMADO',
            created_by=user1,
            atendido_por=user_taller_test,
            fecha_atencion=timezone.now() - timedelta(days=1),
        )
        turno7.save()
        HistorialTurno.objects.create(
            turno=turno7, accion='CREACION',
            descripcion=f'Turno creado para {clientes[1].nombre_completo}',
            usuario=user1,
        )
        HistorialTurno.objects.create(
            turno=turno7, accion='ATENCION_REGISTRADA',
            descripcion=f'Turno confirmado por {user_taller_test.get_full_name()}',
            usuario=user_taller_test,
        )
        msgs_turnos.append(f'Turno {turno7.codigo} - CONFIRMADO ayer (circuito completo, atendido por operador_taller)')

        secciones.append({'titulo': 'Turnos de Prueba', 'mensajes': msgs_turnos})

        # Resumen de contraseñas
        msgs_resumen = [
            '20371056255 / Pastillas992$ (Superadmin)',
            'admin / Pioli2026$ (Superadmin)',
            'operador_admin / Test1234$ (Administracion)',
            'operador_taller / Test1234$ (Taller)',
        ]
        secciones.append({'titulo': 'Credenciales', 'mensajes': msgs_resumen})

        return {
            'titulo': 'Sistema iniciado con DATOS DE PRUEBA correctamente',
            'secciones': secciones,
        }


# Inline para GroupProfile
class GroupProfileInline(admin.StackedInline):
    model = GroupProfile
    can_delete = False
    verbose_name_plural = 'Configuración del Panel'
    min_num = 1
    max_num = 1


# Inline para MenuGrupo dentro de Group
class MenuGrupoInline(admin.TabularInline):
    model = MenuGrupo
    extra = 1
    ordering = ('orden',)
    fields = ('nombre', 'url', 'orden', 'userPermission', 'status')


# Desregistrar el admin por defecto de Group
admin.site.unregister(Group)


class CustomGroupAdmin(GroupAdmin):
    """Admin personalizado para Group con perfil del panel y menús"""
    inlines = (GroupProfileInline, MenuGrupoInline)
    list_display = ('name', 'get_icon', 'get_home', 'get_menu_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

    def get_icon(self, obj):
        try:
            if hasattr(obj, 'panel_profile') and obj.panel_profile:
                return obj.panel_profile.icon or '-'
        except GroupProfile.DoesNotExist:
            pass
        return '-'
    get_icon.short_description = 'Icono'

    def get_home(self, obj):
        try:
            if hasattr(obj, 'panel_profile') and obj.panel_profile:
                return obj.panel_profile.home or '-'
        except GroupProfile.DoesNotExist:
            pass
        return '-'
    get_home.short_description = 'URL Home'

    def get_menu_count(self, obj):
        return obj.menugrupo_set.filter(status=True).count()
    get_menu_count.short_description = 'Menús'

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        for inline_class in self.inlines:
            inline = inline_class(self.model, self.admin_site)
            # Solo mostrar GroupProfileInline si el objeto existe
            if inline_class == GroupProfileInline and obj:
                GroupProfile.objects.get_or_create(group=obj)
            inline_instances.append(inline)
        return inline_instances

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Crear perfil automáticamente al crear grupo
        if not change:
            GroupProfile.objects.get_or_create(group=obj)


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'status')
    list_filter = ('status',)
    search_fields = ('nombre',)


@admin.register(MenuGrupo)
class MenuGrupoAdmin(admin.ModelAdmin):
    list_display = ('grupo', 'nombre', 'url', 'orden', 'userPermission', 'status')
    list_filter = ('grupo', 'status', 'userPermission')
    search_fields = ('nombre', 'url')
    ordering = ('grupo', 'orden')
    change_list_template = 'admin/panel_administracion/menugrupo_change_list.html'

    # =====================================================
    # CONFIGURACIÓN CANÓNICA DEL MENÚ
    # Modificar aquí para agregar/cambiar menús del panel
    # =====================================================
    # Permiso que restringe menús avanzados (Dashboard, Configuraciones, Uso IA)
    # Superusers ven todo sin necesitar este permiso
    PERMISO_ADMINISTRADOR = 'Administrador'

    MENU_CONFIG = [
        {
            'grupo_name': 'Inicio',
            'icon': 'icon-home',
            'home': '/panel/',
            'orden': 0,
            'menus': [
                {'nombre': 'Dashboard Turnos', 'url': '/panel/turnos/dashboard/', 'orden': 1},
                {'nombre': 'Dashboard IA', 'url': '/panel/asistente/dashboard/', 'orden': 2},
            ],
        },
        {
            'grupo_name': 'Administración',
            'icon': 'icon-settings',
            'home': '/panel/',
            'orden': 1,
            'menus': [
                {'nombre': 'Gestión Usuarios', 'url': '/panel/usuarios/', 'orden': 1},
                {'nombre': 'Gestión Sitio', 'url': '/panel/sitio/', 'orden': 2},
            ],
        },
        {
            'grupo_name': 'Asistente IA',
            'icon': 'icon-bubbles',
            'home': '/panel/asistente/config/',
            'orden': 2,
            'menus': [
                {'nombre': 'Preguntas Frecuentes', 'url': '/panel/asistente/faqs/', 'orden': 1},
                {'nombre': 'Base de Conocimiento', 'url': '/panel/asistente/kb/', 'orden': 2},
                {'nombre': 'Conversaciones', 'url': '/panel/asistente/conversaciones/', 'orden': 3},
                {'nombre': 'Sugerencias', 'url': '/panel/asistente/sugerencias/', 'orden': 4},
                {'nombre': 'Uso IA / Costos', 'url': '/panel/asistente/uso-ia/', 'orden': 5, 'permission': 'Administrador'},
                {'nombre': 'Configuración', 'url': '/panel/asistente/config/', 'orden': 6},
            ],
        },
        {
            'grupo_name': 'Turnos',
            'icon': 'icon-calendar',
            'home': '/panel/turnos/',
            'orden': 3,
            'menus': [
                {'nombre': 'Gestión Turnos', 'url': '/panel/turnos/', 'orden': 1},
                {'nombre': 'Escanear Turno', 'url': '/panel/turnos/escanear/', 'orden': 2},
                {'nombre': 'Configuraciones', 'url': '/panel/parametros/', 'orden': 3, 'permission': 'Administrador'},
            ],
        },
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'sincronizar/',
                self.admin_site.admin_view(self.sincronizar_menu),
                name='panel_administracion_menugrupo_sincronizar'
            ),
        ]
        return custom_urls + urls

    def sincronizar_menu(self, request):
        """Sincroniza el menú del panel con la configuración canónica."""
        if request.method == 'POST':
            resultado = self._ejecutar_sincronizacion()
            context = {
                **self.admin_site.each_context(request),
                'title': 'Sincronizar Menú del Panel',
                'resultado': resultado,
                'grupos_count': Group.objects.count(),
                'perfiles_count': GroupProfile.objects.count(),
                'menus_count': MenuGrupo.objects.filter(status=True).count(),
            }
            messages.success(request, 'Menú del panel sincronizado correctamente.')
            return render(request, 'admin/panel_administracion/sincronizar_menu.html', context)

        # GET: mostrar preview
        config_preview = []
        for grupo_cfg in self.MENU_CONFIG:
            preview = {
                'name': grupo_cfg['grupo_name'],
                'icon': grupo_cfg['icon'],
                'home': grupo_cfg['home'],
                'orden': grupo_cfg['orden'],
                'menus': [
                    {
                        'nombre': m['nombre'],
                        'url': m['url'],
                        'orden': m['orden'],
                        'permission': m.get('permission', ''),
                    }
                    for m in grupo_cfg['menus']
                ],
            }
            config_preview.append(preview)

        context = {
            **self.admin_site.each_context(request),
            'title': 'Sincronizar Menú del Panel',
            'config_preview': config_preview,
            'grupos_count': Group.objects.count(),
            'perfiles_count': GroupProfile.objects.count(),
            'menus_count': MenuGrupo.objects.filter(status=True).count(),
        }
        return render(request, 'admin/panel_administracion/sincronizar_menu.html', context)

    def _ejecutar_sincronizacion(self):
        """Ejecuta la sincronización del menú y retorna el log de cambios."""
        resultado = []

        for grupo_cfg in self.MENU_CONFIG:
            seccion = {'titulo': f"Grupo: {grupo_cfg['grupo_name']}", 'mensajes': []}

            # 1. Crear/obtener grupo
            grupo, created = Group.objects.get_or_create(name=grupo_cfg['grupo_name'])
            if created:
                seccion['mensajes'].append(f'Grupo "{grupo.name}" creado')
            else:
                seccion['mensajes'].append(f'Grupo "{grupo.name}" ya existe')

            # 2. Crear/actualizar perfil de grupo
            profile, p_created = GroupProfile.objects.get_or_create(group=grupo)
            profile.icon = grupo_cfg['icon']
            profile.home = grupo_cfg['home']
            profile.orden = grupo_cfg['orden']
            profile.save()
            if p_created:
                seccion['mensajes'].append(
                    f'Perfil creado (icon: {profile.icon}, home: {profile.home}, orden: {profile.orden})'
                )
            else:
                seccion['mensajes'].append(
                    f'Perfil actualizado (icon: {profile.icon}, home: {profile.home}, orden: {profile.orden})'
                )

            # 3. Crear/actualizar menús
            for menu_cfg in grupo_cfg['menus']:
                # Buscar permiso si aplica
                permission = None
                if menu_cfg.get('permission'):
                    permission, _ = UserPermission.objects.get_or_create(
                        nombre=menu_cfg['permission'],
                        defaults={'status': True}
                    )

                menu, m_created = MenuGrupo.objects.get_or_create(
                    grupo=grupo,
                    nombre=menu_cfg['nombre'],
                    defaults={
                        'url': menu_cfg['url'],
                        'orden': menu_cfg['orden'],
                        'userPermission': permission,
                        'status': True,
                    }
                )
                if not m_created:
                    # Actualizar datos existentes
                    menu.url = menu_cfg['url']
                    menu.orden = menu_cfg['orden']
                    menu.userPermission = permission
                    menu.status = True
                    menu.save()
                    seccion['mensajes'].append(
                        f'Menú "{menu_cfg["nombre"]}" actualizado (url: {menu_cfg["url"]}, orden: {menu_cfg["orden"]})'
                    )
                else:
                    seccion['mensajes'].append(
                        f'Menú "{menu_cfg["nombre"]}" creado (url: {menu_cfg["url"]}, orden: {menu_cfg["orden"]})'
                    )

            resultado.append(seccion)

        return resultado


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'status')
    list_filter = ('status',)
    search_fields = ('nombre',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sector', 'userPermission')
    list_filter = ('sector', 'userPermission')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)


@admin.register(GroupProfile)
class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ('group', 'icon', 'home')
    search_fields = ('group__name',)


# Registrar los admins personalizados
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)
