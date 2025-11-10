from django.db import models
from django.core.exceptions import ValidationError


class Service(models.Model):
    """Modelo para los servicios mostrados en la página"""
    icon = models.CharField(max_length=50, help_text="Clase de FontAwesome (ej: fa-shopping-cart)")
    title = models.CharField(max_length=100, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    excel_file = models.FileField(
        upload_to='service/excel/',
        blank=True,
        null=True,
        verbose_name="Archivo Excel de tabla de precios",
        help_text="Sube una tabla de precios en formato Excel (xlsx, xls). Se mostrará como tabla en la descripción si está presente.")
    order = models.IntegerField(default=0, verbose_name="Orden")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def get_excel_table_html(self):
        """Convierte el archivo Excel en una tabla HTML si existe."""
        if self.excel_file:
            try:
                import pandas as pd
                excel_path = self.excel_file.path
                df = pd.read_excel(excel_path, header=None)
                # Opcional: puedes personalizar el estilo de la tabla aquí
                return df.to_html(index=False, header=False, classes="table table-bordered table-striped", border=0)
            except Exception as e:
                return f"<div class='alert alert-warning'>No se pudo mostrar la tabla de precios: {e}</div>"
        return None


class PortfolioItem(models.Model):
    """Modelo para los items del portafolio"""
    title = models.CharField(max_length=100, verbose_name="Título")
    subtitle = models.CharField(max_length=100, verbose_name="Subtítulo/Categoría")
    thumbnail = models.ImageField(upload_to='portfolio/thumbnails/', verbose_name="Imagen miniatura")
    full_image = models.ImageField(upload_to='portfolio/full/', verbose_name="Imagen completa")
    description = models.TextField(verbose_name="Descripción")
    client = models.CharField(max_length=100, verbose_name="Cliente")
    category = models.CharField(max_length=100, verbose_name="Categoría")
    order = models.IntegerField(default=0, verbose_name="Orden")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portafolio"
        verbose_name_plural = "Portafolios"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class TimelineEvent(models.Model):
    """Modelo para eventos de la línea de tiempo (About)"""
    date = models.CharField(max_length=50, verbose_name="Fecha/Período")
    title = models.CharField(max_length=100, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(upload_to='timeline/', verbose_name="Imagen", blank=True, null=True)
    order = models.IntegerField(default=0, verbose_name="Orden")
    inverted = models.BooleanField(default=False, verbose_name="Invertido",
                                   help_text="Alterna el lado de visualización")
    is_final = models.BooleanField(default=False, verbose_name="Es el item final",
                                   help_text="Marca si es el último item 'Be Part Of Our Story'")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evento de Línea de Tiempo"
        verbose_name_plural = "Eventos de Línea de Tiempo"
        ordering = ['order', 'date']

    def __str__(self):
        return f"{self.date} - {self.title}"


class TeamMember(models.Model):
    """Modelo para miembros del equipo"""
    name = models.CharField(max_length=100, verbose_name="Nombre completo")
    position = models.CharField(max_length=100, verbose_name="Cargo/Posición")
    photo = models.ImageField(upload_to='team/', verbose_name="Foto")
    twitter_url = models.URLField(blank=True, verbose_name="URL de Twitter")
    facebook_url = models.URLField(blank=True, verbose_name="URL de Facebook")
    linkedin_url = models.URLField(blank=True, verbose_name="URL de LinkedIn")
    order = models.IntegerField(default=0, verbose_name="Orden")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Miembro del Equipo"
        verbose_name_plural = "Miembros del Equipo"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.position}"


class ContactMessage(models.Model):
    """Modelo para mensajes de contacto recibidos"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    message = models.TextField(verbose_name="Mensaje")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de recepción")
    read = models.BooleanField(default=False, verbose_name="Leído")
    replied = models.BooleanField(default=False, verbose_name="Respondido")

    class Meta:
        verbose_name = "Mensaje de Contacto"
        verbose_name_plural = "Mensajes de Contacto"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class SiteConfiguration(models.Model):
    hero_card_bg_opacity = models.FloatField(
        default=0.85,
        verbose_name='Opacidad del fondo de la card hero',
        help_text='Valor entre 0 (transparente) y 1 (opaco). Ejemplo: 0.85')
    # Card Hero (título/subtítulo)
    hero_card_bg_color = models.CharField(
        max_length=20,
        default='#212529',
        verbose_name='Color de fondo de la card hero',
        help_text='Ejemplo: #212529, #ffffff, rgba(0,0,0,0.1)')
    navbar_bg_color_scrolled = models.CharField(
        max_length=20,
        default='#272EF5',
        verbose_name='Color de fondo del navbar al hacer scroll',
        help_text='Ejemplo: #272EF5, #ffffff, rgba(0,0,0,0.1)')
    hero_card_bg_image = models.ImageField(
        upload_to='hero_card_bg/', blank=True, null=True,
        verbose_name='Imagen de fondo de la card hero',
        help_text='Imagen que se mostrará como fondo en la card hero. Tiene prioridad sobre el color.')
    hero_card_elevation = models.CharField(
        max_length=10,
        default='8px',
        verbose_name='Elevación (sombra) de la card hero',
        help_text='Ejemplo: 8px, 16px')
    hero_card_hover_elevation = models.CharField(
        max_length=10,
        default='24px',
        verbose_name='Elevación hover de la card hero',
        help_text='Ejemplo: 24px, 32px')
    contact_btn_hover_bgcolor = models.CharField(
        max_length=20,
        default='#ffd700',
        verbose_name='Color de fondo del botón de contacto (hover)',
        help_text='Color de fondo del botón cuando el mouse pasa por encima. Ejemplo: #ffd700, #212529, rgba(255,200,0,0.9)')
    # Configuración del botón Enviar en contacto
    contact_btn_text = models.CharField(
        max_length=50,
        default='Enviar Mensaje',
        verbose_name='Texto del botón de contacto',
        help_text='Texto que aparece en el botón de enviar del formulario de contacto.')
    contact_btn_bgcolor = models.CharField(
        max_length=20,
        default='#ffc800',
        verbose_name='Color de fondo del botón de contacto',
        help_text='Ejemplo: #ffc800, #212529, rgba(255,200,0,0.9)')
    contact_btn_fgcolor = models.CharField(
        max_length=20,
        default='#212529',
        verbose_name='Color de texto del botón de contacto',
        help_text='Ejemplo: #fff, #212529')
    # Color de fondo al hacer hover sobre las imágenes del portfolio
    portfolio_hover_bgcolor = models.CharField(
        max_length=20,
        default='#e0e0e0',
        verbose_name='Color de fondo hover en portfolio',
        help_text='Ejemplo: #e0e0e0, #ffffff, rgba(0,0,0,0.1)')
    # Colores de íconos de servicios
    service_icon_bgcolor = models.CharField(
        max_length=20,
        default='#ffc800',
        verbose_name='Color de fondo del ícono (círculo)',
        help_text='Ejemplo: #ffc800 o text-primary')
    service_icon_fgcolor = models.CharField(
        max_length=20,
        default='#02197A',
        verbose_name='Color del ícono (FA)',
        help_text='Ejemplo: #02197A o text-inverse')
    # Configuración de botones del header
    header_btn1_text = models.CharField(
        max_length=100,
        default='Turno Planta Palpalá',
        verbose_name='Texto botón 1')
    header_btn1_url = models.URLField(
        default='https://turnos.redsoft.com.ar/agen',
        verbose_name='URL botón 1')
    header_btn2_text = models.CharField(
        max_length=100,
        default='Turno Planta Libertador',
        verbose_name='Texto botón 2')
    header_btn2_url = models.URLField(
        default='https://turnos.redsoft.com.ar/agenda/calendario',
        verbose_name='URL botón 2')
    header_btn_bgcolor = models.CharField(
        max_length=7,
        default='#02197A',
        verbose_name='Color de fondo de los botones',
        help_text='Formato hex (ej: #02197A)')
    # Configuración de tamaño del video de fondo
    header_video_width = models.CharField(
        max_length=10,
        default='100%',
        verbose_name='Ancho del video de fondo',
        help_text='Ejemplo: 100%, 1920px, 80vw')
    header_video_height = models.CharField(
        max_length=10,
        default='100%',
        verbose_name='Alto del video de fondo',
        help_text='Ejemplo: 100%, 600px, 50vh')
    # Opciones de filtro para el video de fondo
    header_video_brightness = models.FloatField(
        default=0.5,
        verbose_name='Brillo del video de fondo',
        help_text='Valor entre 0 (oscuro) y 1 (normal). Recomendado: 0.3 a 0.7')
    header_video_contrast = models.FloatField(
        default=1.0,
        verbose_name='Contraste del video de fondo',
        help_text='Valor 1 = normal, menor para menos contraste, mayor para más contraste.')
    """Modelo Singleton para configuración general del sitio"""

    # Información general
    site_title = models.CharField(max_length=200, default="Agency", verbose_name="Título del sitio")
    site_logo = models.ImageField(upload_to='site/', verbose_name="Logo", blank=True, null=True)

    # Hero section
    hero_title = models.CharField(max_length=200, default="It's Nice To Meet You", verbose_name="Título del Hero")
    hero_subtitle = models.CharField(max_length=200, default="Welcome To Our Studio!", verbose_name="Subtítulo del Hero")
    hero_button_text = models.CharField(max_length=50, default="Tell Me More", verbose_name="Texto del botón")

    # Footer
    footer_copyright = models.CharField(max_length=200, default="Copyright © Your Website 2024",
                                       verbose_name="Copyright del footer")

    # Redes sociales
    twitter_url = models.URLField(blank=True, verbose_name="URL de Twitter")
    facebook_url = models.URLField(blank=True, verbose_name="URL de Facebook")
    linkedin_url = models.URLField(blank=True, verbose_name="URL de LinkedIn")

    # Información de contacto
    contact_email = models.EmailField(blank=True, verbose_name="Email de contacto")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de contacto")
    contact_address = models.TextField(blank=True, verbose_name="Dirección")

    # Personalización de colores
    primary_color = models.CharField(max_length=7, default="#ffc800", verbose_name="Color primario",
                                     help_text="Formato hex (ej: #ffc800)")
    secondary_color = models.CharField(max_length=7, default="#000000", verbose_name="Color secundario",
                                      help_text="Formato hex (ej: #000000)")

    # Personalización de tipografía
    FONT_CHOICES = [
        ('Montserrat', 'Montserrat'),
        ('Roboto', 'Roboto'),
        ('Open Sans', 'Open Sans'),
        ('Lato', 'Lato'),
        ('Poppins', 'Poppins'),
    ]
    font_family = models.CharField(max_length=50, choices=FONT_CHOICES, default='Poppins',
                                   verbose_name="Fuente principal")
    base_font_size = models.IntegerField(default=16, verbose_name="Tamaño base (px)")
    heading_font_size_h1 = models.IntegerField(default=40, verbose_name="Tamaño H1 (px)")
    heading_font_size_h2 = models.IntegerField(default=32, verbose_name="Tamaño H2 (px)")
    heading_font_size_h3 = models.IntegerField(default=24, verbose_name="Tamaño H3 (px)")
    heading_font_size_h4 = models.IntegerField(default=18, verbose_name="Tamaño H4 (px)")

    # Imagen de fondo del header
    header_background = models.ImageField(
        upload_to='site/header/', blank=True, null=True,
        verbose_name='Imagen de fondo del header')

    # Fondo de la sección de contacto
    contact_section_bg_color = models.CharField(
        max_length=20,
        default='#212529',
        verbose_name='Color de fondo de la sección contacto',
        help_text='Ejemplo: #212529, #ffffff, rgba(0,0,0,0.1)')
    contact_section_bg_opacity = models.FloatField(
        default=1.0,
        verbose_name='Opacidad de fondo de la sección contacto',
        help_text='Valor entre 0 (transparente) y 1 (opaco).')
    contact_section_bg_image = models.ImageField(
        upload_to='contact_bg/', blank=True, null=True,
        verbose_name='Imagen de fondo de la sección contacto',
        help_text='Imagen que se mostrará como fondo en la sección contacto. Tiene prioridad sobre el color.')
    contact_section_bg_video = models.FileField(
        upload_to='contact_bg/video/', blank=True, null=True,
        verbose_name='Video de fondo de la sección contacto',
        help_text='Formato recomendado: MP4, WebM. El video se mostrará en lugar de la imagen si está presente.')
    # Video de fondo del header
    header_background_video = models.FileField(
        upload_to='site/header/video/', blank=True, null=True,
        verbose_name='Video de fondo del header',
        help_text='Formato recomendado: MP4, WebM. El video se mostrará en lugar de la imagen si está presente.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sitio"
        verbose_name_plural = "Configuración del Sitio"

    def save(self, *args, **kwargs):
        # Patrón Singleton: solo permitir una instancia
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError('Solo puede existir una configuración del sitio')
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Configuración del Sitio"

    @classmethod
    def get_config(cls):
        """Método helper para obtener la configuración"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
