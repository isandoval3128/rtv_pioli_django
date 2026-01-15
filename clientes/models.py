from django.db import models
from territorios.models import Localidad


class Persona(models.Model):
    """Modelo base para datos personales"""
    # Identificación
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    cuit = models.CharField(max_length=11, null=True, blank=True, verbose_name="CUIT")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")

    # Contacto
    email = models.EmailField(max_length=200, null=True, blank=True, verbose_name="Email")
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name="Teléfono")
    celular = models.CharField(max_length=20, null=True, blank=True, verbose_name="Celular")

    # Ubicación
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Localidad"
    )
    domicilio = models.CharField(max_length=300, null=True, blank=True, verbose_name="Domicilio")

    # Control
    status = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - DNI: {self.dni}"

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"


class Cliente(Persona):
    """Cliente del sistema de turnos - Hereda de Persona"""

    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PENDIENTE_DOCUMENTACION', 'Pendiente de Documentación'),
        ('PENDIENTE_PAGO', 'Pendiente de Pago'),
        ('DOCUMENTACION_INCOMPLETA', 'Documentación Incompleta'),
        ('BLOQUEADO', 'Bloqueado'),
        ('INACTIVO', 'Inactivo'),
    ]

    # Estado del cliente
    estado_cliente = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='ACTIVO',
        verbose_name="Estado del Cliente"
    )

    # Gestión de turnos
    tiene_turnos_pendientes = models.BooleanField(default=False, verbose_name="Tiene Turnos Pendientes")
    cantidad_turnos_realizados = models.IntegerField(default=0, verbose_name="Turnos Realizados")
    cantidad_turnos_cancelados = models.IntegerField(default=0, verbose_name="Turnos Cancelados")
    ultimo_turno_fecha = models.DateField(null=True, blank=True, verbose_name="Último Turno")

    # Documentación
    documentacion_completa = models.BooleanField(default=False, verbose_name="Documentación Completa")
    documentos_faltantes = models.TextField(
        null=True,
        blank=True,
        verbose_name="Documentos Faltantes",
        help_text="Lista de documentos que faltan"
    )
    notas_internas = models.TextField(
        null=True,
        blank=True,
        verbose_name="Notas Internas",
        help_text="Observaciones del personal administrativo"
    )

    # Preferencias de notificación
    acepta_whatsapp = models.BooleanField(default=True, verbose_name="Acepta WhatsApp")
    acepta_email = models.BooleanField(default=True, verbose_name="Acepta Email")
    acepta_sms = models.BooleanField(default=False, verbose_name="Acepta SMS")

    # Control específico
    cliente_activo = models.BooleanField(default=True, verbose_name="Cliente Activo")
    fecha_registro_cliente = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    ultima_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['apellido', 'nombre']

    def puede_solicitar_turno(self):
        """Verifica si el cliente puede solicitar un turno"""
        if self.estado_cliente == 'BLOQUEADO':
            return False, "Cliente bloqueado. Contacte con administración."
        if self.estado_cliente == 'INACTIVO':
            return False, "Cliente inactivo."
        if not self.cliente_activo:
            return False, "Cliente dado de baja."
        return True, "OK"

    def marcar_documentacion_completa(self):
        """Marca la documentación como completa"""
        self.documentacion_completa = True
        self.documentos_faltantes = None
        if self.estado_cliente == 'PENDIENTE_DOCUMENTACION':
            self.estado_cliente = 'ACTIVO'
        self.save()
