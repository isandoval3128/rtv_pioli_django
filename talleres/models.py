from django.db import models
from django.utils import timezone
from territorios.models import Localidad
from clientes.models import Cliente
from ubicacion.models import Ubicacion


class Taller(models.Model):
    """Talleres de RTV - Revisión Técnica Vehicular"""
    # Referencia a Planta/Ubicación (opcional para reutilizar datos)
    planta = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='talleres',
        verbose_name="Planta/Ubicación",
        help_text="Si se selecciona una planta, se usarán sus datos de ubicación y contacto"
    )

    # Campos propios (se usan si NO hay planta asignada)
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Taller")
    direccion = models.CharField(max_length=300, blank=True, verbose_name="Dirección")
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Localidad"
    )
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")

    # Ubicación GPS para el mapa (se usan si NO hay planta asignada)
    latitud = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        null=True,
        blank=True,
        verbose_name="Latitud"
    )
    longitud = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        null=True,
        blank=True,
        verbose_name="Longitud"
    )

    # Horarios de atención
    horario_apertura = models.TimeField(verbose_name="Hora de Apertura")
    horario_cierre = models.TimeField(verbose_name="Hora de Cierre")
    dias_atencion = models.JSONField(
        default=dict,
        help_text='Formato: {"lunes": true, "martes": true, "miercoles": true, ...}',
        verbose_name="Días de Atención"
    )

    # Fechas especiales (feriados, no laborables)
    fechas_no_laborables = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de fechas no disponibles. Formato: ["2024-12-25", "2025-01-01", ...]',
        verbose_name="Fechas No Laborables"
    )

    # Control y metadata
    status = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Taller"
        verbose_name_plural = "Talleres"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.get_nombre()} - {self.get_localidad()}"

    # Propiedades que priorizan datos de la planta si existe
    def get_nombre(self):
        """Retorna el nombre, priorizando el de la planta si existe"""
        return self.planta.nombre if self.planta else self.nombre

    def get_direccion(self):
        """Retorna la dirección, priorizando la de la planta si existe"""
        return self.planta.direccion if self.planta else self.direccion

    def get_localidad(self):
        """Retorna la localidad, priorizando la de la planta si existe"""
        return self.planta.localidad if self.planta else self.localidad

    def get_telefono(self):
        """Retorna el teléfono, priorizando el de la planta si existe"""
        return self.planta.telefono if self.planta else self.telefono

    def get_email(self):
        """Retorna el email, priorizando el de la planta si existe"""
        return self.planta.email if self.planta else self.email

    def get_latitud(self):
        """Retorna la latitud, priorizando la de la planta si existe"""
        if self.planta:
            return self.planta.latitud
        return self.latitud

    def get_longitud(self):
        """Retorna la longitud, priorizando la de la planta si existe"""
        if self.planta:
            return self.planta.longitud
        return self.longitud


class TipoVehiculo(models.Model):
    """Tipos de vehículos y trámites RTO disponibles con tarifas diferenciadas"""

    # Código de trámite (nuevo campo)
    codigo_tramite = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Código de Trámite",
        help_text="Código interno del trámite (ej: TRM-001)"
    )

    # Nombre del trámite (campo existente)
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del Trámite",
        help_text="Ej: RTO: AUTOS - PICK UP - UTILITARIO"
    )

    # Precios diferenciados según tarifa (nuevos campos)
    precio_provincial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio Provincial",
        help_text="Precio para trámites con tarifa provincial"
    )
    precio_nacional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio Nacional",
        help_text="Precio para trámites con tarifa nacional"
    )
    precio_cajutad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio CAJUTAC",
        help_text="Precio para trámites con tarifa CAJUTAC"
    )

    # Precio legacy (mantener para compatibilidad, deprecated)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio (Legacy)",
        help_text="Campo legacy, usar precios específicos"
    )

    # Campos operativos existentes
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción adicional del trámite"
    )
    duracion_minutos = models.IntegerField(
        default=30,
        verbose_name="Duración (minutos)",
        help_text="Tiempo estimado para completar la inspección"
    )
    status = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el trámite está disponible para reserva"
    )

    # Campos de auditoría (nuevos)
    created = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name="Fecha de Creación"
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Tipo de Trámite"
        verbose_name_plural = "Tipos de Trámites"
        ordering = ['codigo_tramite', 'nombre']

    def __str__(self):
        if self.codigo_tramite:
            return f"{self.codigo_tramite} - {self.nombre}"
        return self.nombre

    def get_precio_display(self):
        """Retorna una representación legible de los precios"""
        precios = []
        if self.precio_provincial:
            precios.append(f"Provincial: ${self.precio_provincial:,.0f}")
        if self.precio_nacional:
            precios.append(f"Nacional: ${self.precio_nacional:,.0f}")
        if self.precio_cajutad:
            precios.append(f"CAJUTAC: ${self.precio_cajutad:,.0f}")
        return " | ".join(precios) if precios else "Sin precios"

    @property
    def nombre_tramite(self):
        """Alias para compatibilidad con funciones de importación"""
        return self.nombre

    @property
    def nombre_normalizado(self):
        """Retorna el nombre en mayúsculas y formato presentable"""
        return self.nombre.upper() if self.nombre else ""

    def save(self, *args, **kwargs):
        """
        Al cambiar el status de TipoVehiculo, sincroniza el status
        de todas las ConfiguracionTaller relacionadas
        """
        # Detectar cambio de status
        if self.pk:  # Si ya existe
            try:
                old_instance = TipoVehiculo.objects.get(pk=self.pk)
                status_cambio = old_instance.status != self.status
            except TipoVehiculo.DoesNotExist:
                status_cambio = False
        else:
            status_cambio = False

        # Guardar el modelo
        super().save(*args, **kwargs)

        # Si cambió el status, actualizar ConfiguracionTaller
        if status_cambio:
            ConfiguracionTaller.objects.filter(tipo_vehiculo=self).update(status=self.status)
            print(f"Status de ConfiguracionTaller actualizado para {self.nombre}: {self.status}")


class ConfiguracionTaller(models.Model):
    """Configuración de horarios y capacidad por taller y tipo de vehículo"""
    taller = models.ForeignKey(
        Taller,
        on_delete=models.CASCADE,
        related_name='configuraciones',
        verbose_name="Taller"
    )
    tipo_vehiculo = models.ForeignKey(
        TipoVehiculo,
        on_delete=models.CASCADE,
        verbose_name="Tipo de Vehículo"
    )

    # Configuración de capacidad
    turnos_simultaneos = models.IntegerField(
        default=2,
        verbose_name="Turnos Simultáneos",
        help_text="Cantidad de vehículos que pueden atenderse al mismo tiempo"
    )
    intervalo_minutos = models.IntegerField(
        default=30,
        verbose_name="Intervalo entre turnos (minutos)",
        help_text="Tiempo entre cada turno disponible"
    )

    # Estado de disponibilidad
    status = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text="Indica si este trámite está disponible en este taller"
    )

    class Meta:
        verbose_name = "Taller - Tipo Trámite"
        verbose_name_plural = "Talleres - Tipos Trámite"
        unique_together = ['taller', 'tipo_vehiculo']

    def __str__(self):
        return f"{self.taller.get_nombre()} - {self.tipo_vehiculo.nombre}"


class Vehiculo(models.Model):
    """Vehículos registrados en el sistema"""
    dominio = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Dominio",
        help_text="Patente del vehículo (ej: ABC123 o AB123CD)"
    )
    marca = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Marca",
        help_text="Marca del vehículo (ej: Ford, Chevrolet, Fiat)"
    )
    modelo = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Modelo",
        help_text="Modelo del vehículo (ej: Focus, Corsa, Palio)"
    )
    tipo_vehiculo = models.ForeignKey(
        TipoVehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo de Vehículo",
        help_text="Opcional - El tipo de trámite se define al crear el turno"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='vehiculos',
        verbose_name="Cliente (Titular)",
        help_text="Cliente responsable del vehículo"
    )
    tiene_gnc = models.BooleanField(
        default=False,
        verbose_name="¿Tiene GNC?",
        help_text="Indica si el vehículo tiene instalación de Gas Natural Comprimido"
    )

    # Control y metadata
    status = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['dominio']

    def __str__(self):
        return f"{self.dominio} - {self.cliente.nombre_completo}"
