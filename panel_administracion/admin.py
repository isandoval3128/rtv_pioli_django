from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
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
    MENU_CONFIG = [
        {
            'grupo_name': 'Administración',
            'icon': 'icon-settings',
            'home': '/panel/',
            'orden': 1,
            'menus': [
                {'nombre': 'Gestión Usuarios', 'url': '/panel/usuarios/', 'orden': 1},
            ],
        },
        {
            'grupo_name': 'Asistente IA',
            'icon': 'icon-bubbles',
            'home': '/panel/asistente/config/',
            'orden': 2,
            'menus': [
                {'nombre': 'Dashboard', 'url': '/panel/asistente/dashboard/', 'orden': 1},
                {'nombre': 'Configuración', 'url': '/panel/asistente/config/', 'orden': 2},
                {'nombre': 'Preguntas Frecuentes', 'url': '/panel/asistente/faqs/', 'orden': 3},
                {'nombre': 'Base de Conocimiento', 'url': '/panel/asistente/kb/', 'orden': 4},
                {'nombre': 'Conversaciones', 'url': '/panel/asistente/conversaciones/', 'orden': 5},
                {'nombre': 'Sugerencias', 'url': '/panel/asistente/sugerencias/', 'orden': 6},
                {'nombre': 'Uso IA / Costos', 'url': '/panel/asistente/uso-ia/', 'orden': 7, 'permission': 'Acceso Uso IA'},
            ],
        },
        {
            'grupo_name': 'Turnos',
            'icon': 'icon-calendar',
            'home': '/panel/turnos/',
            'orden': 3,
            'menus': [
                {'nombre': 'Dashboard', 'url': '/panel/turnos/dashboard/', 'orden': 1},
                {'nombre': 'Gestión Turnos', 'url': '/panel/turnos/', 'orden': 2},
                {'nombre': 'Escanear Turno', 'url': '/panel/turnos/escanear/', 'orden': 3},
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
