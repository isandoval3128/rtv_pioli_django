from django.contrib import admin
from django.utils.html import format_html
from .models import Service, PortfolioItem, TimelineEvent, TeamMember, ContactMessage, SiteConfiguration


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin para el modelo Service"""
    list_display = ['title', 'icon', 'order', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['order', 'active']
    ordering = ['order', 'title']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información del Servicio', {
            'fields': ('icon', 'title', 'description', 'attachment')
        }),
        ('Configuración', {
            'fields': ('order', 'active')
        }),
    )


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    """Admin para el modelo PortfolioItem"""
    list_display = ['title', 'subtitle', 'client', 'category', 'thumbnail_preview', 'order', 'active']
    list_filter = ['active', 'category', 'created_at']
    search_fields = ['title', 'subtitle', 'client', 'description']
    list_editable = ['order', 'active']
    ordering = ['order', 'title']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información del Proyecto', {
            'fields': ('title', 'subtitle', 'client', 'category', 'description')
        }),
        ('Imágenes', {
            'fields': ('thumbnail', 'full_image')
        }),
        ('Configuración', {
            'fields': ('order', 'active')
        }),
    )

    def thumbnail_preview(self, obj):
        """Muestra preview de la imagen thumbnail"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.thumbnail.url
            )
        return '-'
    thumbnail_preview.short_description = 'Preview'


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    """Admin para el modelo TimelineEvent"""
    list_display = ['date', 'title', 'order', 'inverted', 'is_final', 'active']
    list_filter = ['active', 'inverted', 'is_final', 'created_at']
    search_fields = ['date', 'title', 'description']
    list_editable = ['order', 'inverted', 'is_final', 'active']
    ordering = ['order', 'date']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información del Evento', {
            'fields': ('date', 'title', 'description', 'image')
        }),
        ('Configuración', {
            'fields': ('order', 'inverted', 'is_final', 'active')
        }),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin para el modelo TeamMember"""
    list_display = ['name', 'position', 'photo_preview', 'order', 'active', 'has_social_links']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'position']
    list_editable = ['order', 'active']
    ordering = ['order', 'name']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información Personal', {
            'fields': ('name', 'position', 'photo')
        }),
        ('Redes Sociales', {
            'fields': ('twitter_url', 'facebook_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('order', 'active')
        }),
    )

    def photo_preview(self, obj):
        """Muestra preview de la foto"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />',
                obj.photo.url
            )
        return '-'
    photo_preview.short_description = 'Foto'

    def has_social_links(self, obj):
        """Indica si tiene redes sociales configuradas"""
        has_links = any([obj.twitter_url, obj.facebook_url, obj.linkedin_url])
        if has_links:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_social_links.short_description = 'Redes'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin para el modelo ContactMessage"""
    list_display = ['name', 'email', 'phone', 'created_at', 'read', 'replied']
    list_filter = ['read', 'replied', 'created_at']
    search_fields = ['name', 'email', 'phone', 'message']
    readonly_fields = ['name', 'email', 'phone', 'message', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Información del Contacto', {
            'fields': ('name', 'email', 'phone', 'created_at')
        }),
        ('Mensaje', {
            'fields': ('message',)
        }),
        ('Estado', {
            'fields': ('read', 'replied')
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_replied']

    def mark_as_read(self, request, queryset):
        """Acción para marcar como leído"""
        updated = queryset.update(read=True)
        self.message_user(request, f'{updated} mensaje(s) marcado(s) como leído(s).')
    mark_as_read.short_description = 'Marcar como leído'

    def mark_as_unread(self, request, queryset):
        """Acción para marcar como no leído"""
        updated = queryset.update(read=False)
        self.message_user(request, f'{updated} mensaje(s) marcado(s) como no leído(s).')
    mark_as_unread.short_description = 'Marcar como no leído'

    def mark_as_replied(self, request, queryset):
        """Acción para marcar como respondido"""
        updated = queryset.update(replied=True, read=True)
        self.message_user(request, f'{updated} mensaje(s) marcado(s) como respondido(s).')
    mark_as_replied.short_description = 'Marcar como respondido'


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin para el modelo SiteConfiguration (Singleton)"""

    fieldsets = (
            ('Información General', {
            'fields': ('site_title', 'site_logo', 'header_background', 'header_background_video', 'header_video_brightness', 'header_video_contrast', 'header_video_width', 'header_video_height', 'header_btn1_text', 'header_btn1_url', 'header_btn2_text', 'header_btn2_url', 'header_btn_bgcolor', 'service_icon_bgcolor', 'service_icon_fgcolor', 'portfolio_hover_bgcolor', 'contact_section_bg_color', 'contact_section_bg_opacity', 'contact_section_bg_image', 'contact_section_bg_video', 'contact_btn_text', 'contact_btn_bgcolor', 'contact_btn_fgcolor', 'contact_btn_hover_bgcolor', 'hero_card_bg_color', 'navbar_bg_color_scrolled', 'hero_card_bg_image', 'hero_card_elevation', 'hero_card_hover_elevation', 'hero_card_bg_opacity')
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_button_text')
        }),
        ('Footer', {
            'fields': ('footer_copyright',)
        }),
        ('Redes Sociales', {
            'fields': ('twitter_url', 'facebook_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('Información de Contacto', {
            'fields': ('contact_email', 'contact_phone', 'contact_address'),
            'classes': ('collapse',)
        }),
        ('Colores', {
            'fields': ('primary_color', 'secondary_color'),
            'description': 'Personalización de colores del sitio'
        }),
        ('Tipografía', {
            'fields': ('font_family', 'base_font_size', 'heading_font_size_h1',
                      'heading_font_size_h2', 'heading_font_size_h3', 'heading_font_size_h4'),
            'description': 'Personalización de fuentes y tamaños'
        }),
    )

    def has_add_permission(self, request):
        """Prevenir la creación de múltiples configuraciones"""
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Prevenir la eliminación de la configuración"""
        return False
