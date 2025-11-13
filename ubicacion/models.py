from django.db import models

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50, blank=True)
    provincia = models.CharField(max_length=100, default="Jujuy")
    horario = models.CharField(max_length=255, blank=True)
    latitud = models.FloatField()
    longitud = models.FloatField()
    orden = models.IntegerField(null=True, blank=True, help_text="Orden de aparición en la lista")

    def __str__(self):
        return self.nombre
