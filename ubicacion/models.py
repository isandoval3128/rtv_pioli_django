from django.db import models
from territorios.models import Localidad


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    provincia = models.CharField(max_length=100, default="Jujuy", verbose_name="Provincia")
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ubicaciones',
        verbose_name="Localidad"
    )
    horario = models.CharField(max_length=255, blank=True, verbose_name="Horario de atención")
    latitud = models.FloatField(verbose_name="Latitud")
    longitud = models.FloatField(verbose_name="Longitud")
    orden = models.IntegerField(null=True, blank=True, help_text="Orden de aparición en la lista", verbose_name="Orden")

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre
