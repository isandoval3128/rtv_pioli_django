from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    """Sectores de los usuarios (ej: Administración, Contable, Taller, etc.)"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    status = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class UserProfile(models.Model):
    """Perfil extendido del usuario"""
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
        verbose_name="Sector"
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
