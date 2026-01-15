from django.db import models
from django.core.exceptions import ValidationError


class Departamento(models.Model):
    """Departamentos de la provincia"""
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    codigo = models.CharField(max_length=50, null=True, blank=True, verbose_name="Código")
    status = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Municipio(models.Model):
    """Municipios - Siempre pertenecen a un Departamento"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    codigo = models.CharField(max_length=50, verbose_name="Código")
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name='municipios',
        verbose_name="Departamento"
    )
    domicilio = models.CharField(max_length=300, null=True, blank=True, verbose_name="Domicilio")
    latitud = models.CharField(max_length=50, null=True, blank=True, verbose_name="Latitud")
    longitud = models.CharField(max_length=50, null=True, blank=True, verbose_name="Longitud")
    status = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        ordering = ['departamento__nombre', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.departamento.nombre}"


class Localidad(models.Model):
    """
    Localidades - Siempre pertenecen a un Departamento.
    Opcionalmente pueden pertenecer a un Municipio.
    Si tiene Municipio, debe ser del mismo Departamento.
    """
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name='localidades',
        verbose_name="Departamento"
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='localidades',
        verbose_name="Municipio (Opcional)"
    )
    codigo_postal = models.CharField(max_length=10, null=True, blank=True, verbose_name="Código Postal")
    status = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Localidad"
        verbose_name_plural = "Localidades"
        ordering = ['departamento__nombre', 'nombre']

    def __str__(self):
        if self.municipio:
            return f"{self.nombre} - {self.municipio.nombre} - {self.departamento.nombre}"
        return f"{self.nombre} - {self.departamento.nombre}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo con jerarquía territorial"""
        return self.__str__()

    def clean(self):
        """Validar que si tiene municipio, pertenezca al mismo departamento"""
        if self.municipio and self.municipio.departamento != self.departamento:
            raise ValidationError({
                'municipio': f"El municipio '{self.municipio.nombre}' no pertenece al departamento '{self.departamento.nombre}'"
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
