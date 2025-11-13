from django.db import models

class Tarifa(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    archivo_excel = models.FileField(upload_to='tarifas/', blank=True, null=True)

    def __str__(self):
        return self.titulo
