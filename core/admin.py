from django.contrib import admin
from .models import AboutSection, AboutImage, EmailConfig, WhatsAppConfig
from django.contrib import admin
from django.utils.html import format_html
from .models import Service, PortfolioItem, TimelineEvent, ContactMessage, SiteConfiguration
from django import forms

@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'pais', 'codigo_pais', 'provincia', 'numero_local', 'numero_internacional', 'descripcion', 'created_at', 'updated_at']
    search_fields = ['nombre', 'pais', 'provincia', 'numero_local', 'numero_internacional', 'descripcion']
    readonly_fields = ['numero_internacional', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('nombre', 'pais', 'codigo_pais', 'provincia', 'numero_local', 'numero_internacional', 'descripcion', 'created_at', 'updated_at')
        }),
    )

class EmailConfigForm(forms.ModelForm):
    class Meta:
        model = EmailConfig
        fields = '__all__'
        widgets = {
            'email_host_password': forms.PasswordInput(render_value=True, attrs={'style': 'width: 300px;'}),
        }

    class Media:
        js = ('admin/js/emailconfig_password_toggle.js',)

@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    form = EmailConfigForm
    list_display = ['email_host_user', 'contact_admin_email', 'email_host', 'email_port', 'email_use_tls']
    search_fields = ['email_host_user', 'contact_admin_email']
    fieldsets = (
        ('Datos de acceso', {
            'fields': ('email_host_user', 'email_host_password')
        }),
        ('Servidor SMTP', {
            'fields': ('email_host', 'email_port', 'email_use_tls')
        }),
        ('Remitente y destinatario', {
            'fields': ('default_from_email', 'contact_admin_email')
        }),
    )

class AboutImageInline(admin.TabularInline):
    model = AboutImage
    extra = 1
    fields = ('image',)
    show_change_link = True

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'visible']
    search_fields = ['title', 'description']
    list_editable = ['visible']
    inlines = [AboutImageInline]

@admin.register(AboutImage)
class AboutImageAdmin(admin.ModelAdmin):
    list_display = ['about_section', 'image']
    search_fields = ['about_section__title']

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

# @admin.register(TeamMember)
# class TeamMemberAdmin(admin.ModelAdmin):
#     """Admin para el modelo TeamMember"""
"""     list_display = ['name', 'position', 'photo_preview', 'order', 'active', 'has_social_links']
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

        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />',
                obj.photo.url
            )
        return '-'
    photo_preview.short_description = 'Foto'

    def has_social_links(self, obj):
   
        has_links = any([obj.twitter_url, obj.facebook_url, obj.linkedin_url])
        if has_links:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_social_links.short_description = 'Redes' """


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
            'fields': ('site_title', 'site_logo', 'header_background', 'header_background_video', 'header_video_brightness', 'header_video_contrast', 'header_video_width', 'header_video_height', 'header_btn1_text', 'header_btn1_url', 'header_btn2_text', 'header_btn2_url', 'header_btn_bgcolor', 'header_btns_text', 'header_btns_video', 'header_btns_text_color', 'service_icon_bgcolor', 'service_icon_fgcolor', 'portfolio_hover_bgcolor', 'contact_section_bg_color', 'contact_section_bg_opacity', 'contact_section_bg_image', 'contact_section_bg_video', 'contact_btn_text', 'contact_btn_bgcolor', 'contact_btn_fgcolor', 'contact_btn_hover_bgcolor', 'hero_card_bg_color', 'navbar_bg_color_scrolled', 'hero_card_bg_image', 'hero_card_elevation', 'hero_card_hover_elevation', 'hero_card_bg_opacity')
        }),
        ('Hero Section', {
            'fields': ('show_hero_title', 'show_hero_subtitle', 'hero_title', 'hero_subtitle', 'hero_button_text'),
            'description': 'Título y subtítulo del Hero ahora son opcionales.'
        }),
        ('Footer', {
            'fields': ('footer_copyright',)
        }),
        ('Redes Sociales', {
            'fields': ('twitter_url', 'facebook_url', 'instagram_url', 'linkedin_url'),
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
