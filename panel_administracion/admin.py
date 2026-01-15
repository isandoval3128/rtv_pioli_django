from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
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
