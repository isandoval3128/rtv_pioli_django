from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import secrets


class UserPermission(models.Model):
    """Perfiles/Permisos personalizados para usuarios"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Permiso")
    status = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Permiso de Usuario"
        verbose_name_plural = "Permisos de Usuario"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Sector(models.Model):
    """
    Sectores principales del sistema.
    Define el comportamiento al escanear QR de turnos.
    Valores: ADMINISTRACION, TALLER
    """
    SECTOR_ADMINISTRACION = 'ADMINISTRACION'
    SECTOR_TALLER = 'TALLER'

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Codigo",
        help_text="Identificador unico del sector (ADMINISTRACION, TALLER)"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    status = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def es_taller(self):
        return self.codigo == self.SECTOR_TALLER

    @property
    def es_administracion(self):
        return self.codigo == self.SECTOR_ADMINISTRACION


class UserProfile(models.Model):
    """Perfil extendido del usuario"""

    # Roles/Origenes especificos dentro de cada sector
    ORIGEN_CHOICES = [
        # Roles de Administracion
        ('GERENTE', 'Gerente'),
        ('RECURSOS_HUMANOS', 'Recursos Humanos'),
        ('ADMINISTRATIVO', 'Administrativo'),
        # Roles de Taller
        ('OPERARIO_AUTO', 'Operario Auto'),
        ('OPERARIO_CAMION', 'Operario Camion'),
        ('SUPERVISOR_TALLER', 'Supervisor Taller'),
        # General
        ('GENERAL', 'General'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='panel_profile',
        verbose_name="Usuario"
    )
    sector = models.ForeignKey(
        Sector,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Sector",
        help_text="Define el comportamiento al escanear QR de turnos (ADMINISTRACION o TALLER)"
    )
    origen = models.CharField(
        max_length=30,
        choices=ORIGEN_CHOICES,
        default='GENERAL',
        blank=True,
        null=True,
        verbose_name="Rol/Cargo",
        help_text="Rol especifico del usuario dentro del sector"
    )
    userPermission = models.ForeignKey(
        UserPermission,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Permiso"
    )

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"Perfil de {self.user.username}"

    @property
    def es_taller(self):
        """Retorna True si el usuario pertenece al sector Taller"""
        return self.sector and self.sector.codigo == Sector.SECTOR_TALLER

    @property
    def es_administracion(self):
        """Retorna True si el usuario pertenece al sector Administracion"""
        return self.sector and self.sector.codigo == Sector.SECTOR_ADMINISTRACION

    def get_sector_codigo(self):
        """Retorna el codigo del sector o ADMINISTRACION por defecto"""
        if self.sector:
            return self.sector.codigo
        return Sector.SECTOR_ADMINISTRACION


class GroupProfile(models.Model):
    """Perfil extendido del grupo para el panel"""
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name='panel_profile',
        verbose_name="Grupo"
    )
    home = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="URL Home"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Icono",
        help_text="Clase de icono (ej: icon-home, fa fa-users)"
    )

    class Meta:
        verbose_name = "Perfil de Grupo"
        verbose_name_plural = "Perfiles de Grupo"

    def __str__(self):
        return f"Perfil de {self.group.name}"


class MenuGrupo(models.Model):
    """Menú dinámico por grupo de usuario"""
    grupo = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        verbose_name="Grupo"
    )
    url = models.CharField(max_length=200, verbose_name="URL")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Menú")
    orden = models.IntegerField(default=0, verbose_name="Orden")
    userPermission = models.ForeignKey(
        UserPermission,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Permiso Requerido",
        help_text="Si se especifica, solo usuarios con este permiso verán este menú"
    )
    status = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Menú de Grupo"
        verbose_name_plural = "Menús de Grupo"
        ordering = ['grupo', 'orden']

    def __str__(self):
        return f"{self.grupo.name} - {self.nombre}"


# Señales para auto-crear perfiles
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un UserProfile cuando se crea un User"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guarda el UserProfile cuando se guarda el User"""
    if hasattr(instance, 'panel_profile'):
        instance.panel_profile.save()


@receiver(post_save, sender=Group)
def create_group_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un GroupProfile cuando se crea un Group"""
    if created:
        GroupProfile.objects.get_or_create(group=instance)


class PasswordResetToken(models.Model):
    """Token para restablecimiento seguro de contraseña"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name="Usuario"
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    expires_at = models.DateTimeField(
        verbose_name="Fecha de expiración"
    )
    used = models.BooleanField(
        default=False,
        verbose_name="Usado"
    )
    used_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de uso"
    )

    class Meta:
        verbose_name = "Token de Restablecimiento"
        verbose_name_plural = "Tokens de Restablecimiento"
        ordering = ['-created_at']

    def __str__(self):
        return f"Token para {self.user.username} - {'Usado' if self.used else 'Activo'}"

    @classmethod
    def generate_token(cls, user, expiration_hours=24):
        """
        Genera un nuevo token para el usuario.
        Invalida tokens anteriores no usados.
        """
        # Invalidar tokens anteriores no usados
        cls.objects.filter(user=user, used=False).update(used=True)

        # Generar nuevo token
        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timezone.timedelta(hours=expiration_hours)

        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

    @classmethod
    def validate_token(cls, token):
        """
        Valida un token y retorna el objeto si es válido.
        Retorna None si el token es inválido, expirado o ya usado.
        """
        try:
            reset_token = cls.objects.get(token=token, used=False)
            if reset_token.expires_at < timezone.now():
                return None  # Token expirado
            return reset_token
        except cls.DoesNotExist:
            return None

    def mark_as_used(self):
        """Marca el token como usado"""
        self.used = True
        self.used_at = timezone.now()
        self.save()
