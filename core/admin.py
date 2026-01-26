from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from .models import AboutSection, AboutImage, EmailConfig, WhatsAppConfig
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
    list_display = [
        'nombre',
        'es_principal_display',
        'email_host_user',
        'contact_admin_email',
        'email_host',
        'email_port',
        'status',
        'test_button'
    ]
    list_filter = ['es_principal', 'status', 'email_host']
    search_fields = ['nombre', 'email_host_user', 'contact_admin_email']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-es_principal', 'nombre']
    change_list_template = 'admin/core/emailconfig_change_list.html'

    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'es_principal', 'status')
        }),
        ('Datos de acceso', {
            'fields': ('email_host_user', 'email_host_password')
        }),
        ('Servidor SMTP', {
            'fields': ('email_host', 'email_port', 'email_use_tls')
        }),
        ('Remitente y destinatario', {
            'fields': ('default_from_email', 'contact_admin_email')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['marcar_como_principal', 'probar_configuracion']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'test-email/<int:config_id>/',
                self.admin_site.admin_view(self.test_email_view),
                name='core_emailconfig_test'
            ),
        ]
        return custom_urls + urls

    def test_button(self, obj):
        """Muestra un botón para probar la conexión de email"""
        return format_html(
            '<a class="button" href="test-email/{}/" style="background: #17a2b8; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 11px;">Probar</a>',
            obj.pk
        )
    test_button.short_description = 'Test'
    test_button.allow_tags = True

    def test_email_view(self, request, config_id):
        """Vista para probar la configuración de email"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime

        try:
            config = EmailConfig.objects.get(pk=config_id)
        except EmailConfig.DoesNotExist:
            self.message_user(request, "Configuración no encontrada.", messages.ERROR)
            return redirect('admin:core_emailconfig_changelist')

        resultado = {
            'config': config,
            'exito': False,
            'mensaje': '',
            'detalles': [],
            'fecha_test': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }

        try:
            # Paso 1: Conectar al servidor SMTP
            resultado['detalles'].append(('Conectando al servidor SMTP...', 'info'))

            if config.email_use_tls:
                server = smtplib.SMTP(config.email_host, config.email_port, timeout=30)
                resultado['detalles'].append((f'Conexión establecida con {config.email_host}:{config.email_port}', 'success'))

                # Paso 2: Iniciar TLS
                resultado['detalles'].append(('Iniciando conexión TLS...', 'info'))
                server.starttls()
                resultado['detalles'].append(('TLS activado correctamente', 'success'))
            else:
                server = smtplib.SMTP_SSL(config.email_host, config.email_port, timeout=30)
                resultado['detalles'].append((f'Conexión SSL establecida con {config.email_host}:{config.email_port}', 'success'))

            # Paso 3: Autenticación
            resultado['detalles'].append(('Autenticando usuario...', 'info'))
            server.login(config.email_host_user, config.email_host_password)
            resultado['detalles'].append((f'Autenticación exitosa para {config.email_host_user}', 'success'))

            # Paso 4: Enviar email de prueba
            destinatario = config.contact_admin_email or config.email_host_user
            remitente = config.default_from_email or config.email_host_user

            resultado['detalles'].append((f'Enviando email de prueba a {destinatario}...', 'info'))

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Test de Configuración - {config.nombre}'
            msg['From'] = remitente
            msg['To'] = destinatario

            texto_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0;">Conexión Exitosa</h1>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                    <h2>Configuración de Correo</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Nombre:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.nombre}</td></tr>
                        <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Servidor:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.email_host}:{config.email_port}</td></tr>
                        <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Usuario:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.email_host_user}</td></tr>
                        <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>TLS:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{'Sí' if config.email_use_tls else 'No'}</td></tr>
                        <tr><td style="padding: 8px;"><strong>Fecha del test:</strong></td><td style="padding: 8px;">{resultado['fecha_test']}</td></tr>
                    </table>
                </div>
                <p style="color: #666; font-size: 12px; margin-top: 20px; text-align: center;">
                    Este es un email de prueba enviado desde el panel de administración.
                </p>
            </body>
            </html>
            """

            parte_html = MIMEText(texto_html, 'html')
            msg.attach(parte_html)

            server.sendmail(remitente, [destinatario], msg.as_string())
            resultado['detalles'].append((f'Email enviado exitosamente a {destinatario}', 'success'))

            # Cerrar conexión
            server.quit()
            resultado['detalles'].append(('Conexión cerrada correctamente', 'success'))

            resultado['exito'] = True
            resultado['mensaje'] = f'La configuración funciona correctamente. Se envió un email de prueba a {destinatario}.'

        except smtplib.SMTPAuthenticationError as e:
            resultado['detalles'].append((f'Error de autenticación: {str(e)}', 'error'))
            resultado['mensaje'] = 'Error de autenticación. Verifique el usuario y contraseña.'
        except smtplib.SMTPConnectError as e:
            resultado['detalles'].append((f'Error de conexión: {str(e)}', 'error'))
            resultado['mensaje'] = f'No se pudo conectar al servidor {config.email_host}:{config.email_port}.'
        except smtplib.SMTPException as e:
            resultado['detalles'].append((f'Error SMTP: {str(e)}', 'error'))
            resultado['mensaje'] = f'Error de SMTP: {str(e)}'
        except Exception as e:
            resultado['detalles'].append((f'Error inesperado: {str(e)}', 'error'))
            resultado['mensaje'] = f'Error inesperado: {str(e)}'

        context = {
            **self.admin_site.each_context(request),
            'title': f'Test de Email - {config.nombre}',
            'opts': self.model._meta,
            'resultado': resultado,
        }
        return render(request, 'admin/core/emailconfig_test.html', context)

    def es_principal_display(self, obj):
        """Muestra un indicador visual si es la configuración principal"""
        if obj.es_principal:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                '#28a745',
                '✓ Principal'
            )
        return format_html('<span style="color: {};">{}</span>', '#999', '-')
    es_principal_display.short_description = 'Principal'
    es_principal_display.admin_order_field = 'es_principal'

    def marcar_como_principal(self, request, queryset):
        """Acción para marcar una configuración como principal"""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Seleccione exactamente una configuración para marcar como principal.',
                level='error'
            )
            return

        config = queryset.first()
        # Desmarcar todas las demás
        EmailConfig.objects.exclude(pk=config.pk).update(es_principal=False)
        # Marcar la seleccionada
        config.es_principal = True
        config.save()

        self.message_user(
            request,
            f'"{config.nombre}" ahora es la configuración principal de correo.'
        )
    marcar_como_principal.short_description = 'Marcar como configuración principal'

    @admin.action(description="Probar configuración de email seleccionada")
    def probar_configuracion(self, request, queryset):
        """Acción para probar la configuración seleccionada"""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Seleccione exactamente una configuración para probar.',
                messages.WARNING
            )
            return
        config = queryset.first()
        return redirect(f'test-email/{config.pk}/')

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
