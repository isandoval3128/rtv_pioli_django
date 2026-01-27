from django.db import models
from django.utils import timezone
from clientes.models import Cliente
from territorios.models import Localidad
from django.contrib.auth.models import User
from talleres.models import Taller, TipoVehiculo, Vehiculo
import secrets
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw


class Turno(models.Model):
    """Turnos agendados para revisiones técnicas"""
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado'),
        ('EN_CURSO', 'En Curso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
        ('NO_ASISTIO', 'No Asistió'),
    ]

    # Identificación única
    codigo = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        verbose_name="Código de Turno",
        help_text="Código único generado automáticamente"
    )

    # Relaciones principales
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.CASCADE,
        verbose_name="Vehículo",
        related_name='turnos'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='turnos_rtv',
        verbose_name="Cliente",
        help_text="Cliente que agenda el turno"
    )
    taller = models.ForeignKey(
        Taller,
        on_delete=models.CASCADE,
        verbose_name="Taller",
        related_name='turnos'
    )
    tipo_vehiculo = models.ForeignKey(
        TipoVehiculo,
        on_delete=models.CASCADE,
        verbose_name="Tipo de Trámite"
    )

    # Fecha y horario del turno
    fecha = models.DateField(verbose_name="Fecha del Turno")
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(verbose_name="Hora de Finalización")

    # Estado del turno
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name="Estado del Turno"
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Notas adicionales sobre el turno"
    )

    # Control de notificaciones
    email_enviado = models.BooleanField(
        default=False,
        verbose_name="Email de Confirmación Enviado"
    )
    whatsapp_enviado = models.BooleanField(
        default=False,
        verbose_name="WhatsApp Enviado"
    )
    recordatorio_enviado = models.BooleanField(
        default=False,
        verbose_name="Recordatorio Enviado"
    )

    # QR Code y Token de cancelación
    qr_code = models.ImageField(
        upload_to='turnos/qr/',
        blank=True,
        null=True,
        verbose_name="Código QR"
    )
    token_cancelacion = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="Token de Cancelación",
        help_text="Token único para cancelar el turno"
    )

    # Token para reprogramación segura
    token_reprogramacion = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        editable=False,
        verbose_name="Token de Reprogramación",
        help_text="Token único para permitir reprogramación segura del turno"
    )
    token_expiracion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Expiración del Token",
        help_text="Fecha y hora de expiración del token de reprogramación"
    )

    # Timestamps y auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_creados',
        verbose_name="Creado por",
        help_text="Usuario que creó el turno (para turnos desde el admin)"
    )

    # Campos de atencion (cuando se escanea el QR en el taller)
    atendido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_atendidos',
        verbose_name="Atendido por",
        help_text="Usuario del taller que registro la atencion del turno"
    )
    fecha_atencion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Atencion",
        help_text="Fecha y hora en que se registro la atencion del turno"
    )

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['-fecha', '-hora_inicio']
        unique_together = ['taller', 'fecha', 'hora_inicio']
        indexes = [
            models.Index(fields=['fecha', 'taller']),
            models.Index(fields=['codigo']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.vehiculo.dominio} - {self.fecha} {self.hora_inicio}"

    def save(self, *args, **kwargs):
        """Override para generar código y token automáticamente"""
        update_fields = kwargs.get('update_fields')

        # Solo generar código/token si es una creación nueva (sin update_fields)
        if update_fields is None:
            # Generar código único si no existe
            if not self.codigo:
                self.codigo = f"TRN-{secrets.token_hex(3).upper()}"

            # Generar token de cancelación si no existe
            if not self.token_cancelacion:
                self.token_cancelacion = secrets.token_urlsafe(32)

        super().save(*args, **kwargs)

        # Generar QR solo si es nuevo y no estamos haciendo update parcial
        if update_fields is None and not self.qr_code:
            self.generar_qr()

    @staticmethod
    def generar_token_verificacion(codigo):
        """Genera un token HMAC para verificar autenticidad del QR"""
        import hmac
        import hashlib
        from django.conf import settings

        # Usa SECRET_KEY de Django como clave para el HMAC
        key = settings.SECRET_KEY.encode('utf-8')
        message = f"rtv_turno_{codigo}".encode('utf-8')

        # Genera HMAC-SHA256 y toma los primeros 16 caracteres (suficiente seguridad)
        token = hmac.new(key, message, hashlib.sha256).hexdigest()[:16]
        return token

    @staticmethod
    def verificar_token(codigo, token):
        """Verifica si el token es válido para el código dado"""
        import hmac
        token_esperado = Turno.generar_token_verificacion(codigo)
        return hmac.compare_digest(token, token_esperado) if token else False

    def generar_qr(self):
        """Genera código QR con URL de verificación del turno (con token de seguridad)"""
        from django.conf import settings
        import hmac

        # Crear instancia de QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Generar token de verificación HMAC
        token = self.generar_token_verificacion(self.codigo)

        # URL de verificación del turno (página profesional al escanear)
        # Usa SITE_URL_LOCAL si está definido (para desarrollo), sino usa SITE_URL (producción)
        import socket
        hostname = socket.gethostname().lower()

        # Si hay SITE_URL_LOCAL configurado y no estamos en el servidor de producción
        site_url_local = getattr(settings, 'SITE_URL_LOCAL', None)
        site_url_prod = getattr(settings, 'SITE_URL', 'https://rtvpioli.com.ar')

        # Detecta producción por IP del servidor o nombre del host
        es_produccion = '167.71.93.198' in hostname or 'rtvpioli' in hostname or site_url_local is None

        site_url = site_url_prod if es_produccion else site_url_local
        qr_url = f"{site_url}/turnero/verificar/{self.codigo}/?t={token}"

        qr.add_data(qr_url)
        qr.make(fit=True)

        # Crear imagen del QR con colores del tema RTV
        img = qr.make_image(fill_color="#13304d", back_color="white")

        # Guardar en BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Guardar en el modelo
        filename = f'turno_{self.codigo}.png'
        self.qr_code.save(filename, File(buffer), save=True)

    def generar_token_reprogramacion(self):
        """Genera un token único para reprogramar el turno con expiración de 48 horas"""
        from datetime import timedelta

        self.token_reprogramacion = secrets.token_urlsafe(32)
        self.token_expiracion = timezone.now() + timedelta(hours=48)
        self.save(update_fields=['token_reprogramacion', 'token_expiracion'])
        return self.token_reprogramacion

    def token_reprogramacion_valido(self):
        """Verifica si el token de reprogramación es válido"""
        if not self.token_reprogramacion or not self.token_expiracion:
            return False

        return timezone.now() < self.token_expiracion

    @property
    def puede_cancelar(self):
        """Verifica si el turno aún puede ser cancelado"""
        # No se puede cancelar si ya pasó o está en curso/completado
        if self.estado in ['COMPLETADO', 'CANCELADO', 'EN_CURSO']:
            return False

        # No se puede cancelar si es para hoy o ya pasó
        return self.fecha > timezone.now().date()

    @property
    def puede_reprogramar(self):
        """Verifica si el turno puede ser reprogramado"""
        # Solo se puede reprogramar si está PENDIENTE o CONFIRMADO
        if self.estado not in ['PENDIENTE', 'CONFIRMADO']:
            return False

        # Debe faltar al menos 24 horas para el turno
        from datetime import datetime, timedelta
        turno_datetime = datetime.combine(self.fecha, self.hora_inicio)
        ahora = timezone.now()
        diferencia = turno_datetime - ahora.replace(tzinfo=None)

        return diferencia.total_seconds() > (24 * 3600)

    @property
    def dias_para_turno(self):
        """Calcula dias faltantes para el turno"""
        delta = self.fecha - timezone.now().date()
        return delta.days

    def registrar_atencion(self, usuario, ip_address=None):
        """
        Registra la atencion del turno por un usuario del taller.
        Cambia el estado a CONFIRMADO y guarda quien atendio.
        """
        from turnero.models import HistorialTurno

        # Guardar datos de atencion
        self.atendido_por = usuario
        self.fecha_atencion = timezone.now()
        self.estado = 'CONFIRMADO'
        self.save(update_fields=['atendido_por', 'fecha_atencion', 'estado'])

        # Recargar desde la base de datos para asegurar que tenemos los valores actuales
        self.refresh_from_db()

        # Registrar en historial
        HistorialTurno.objects.create(
            turno=self,
            accion='ATENCION_REGISTRADA',
            descripcion=f'Turno confirmado por {usuario.get_full_name() or usuario.username}',
            usuario=usuario,
            ip_address=ip_address
        )

        return True

    @property
    def ya_fue_atendido(self):
        """Verifica si el turno ya fue atendido"""
        return self.atendido_por is not None or self.estado in ['EN_CURSO', 'COMPLETADO']


class HistorialTurno(models.Model):
    """Historial de cambios y acciones sobre turnos (auditoría)"""
    turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name="Turno"
    )
    accion = models.CharField(
        max_length=50,
        verbose_name="Acción",
        help_text="Tipo de acción realizada (creación, modificación, cancelación, etc.)"
    )
    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Detalle de la acción realizada"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario",
        help_text="Usuario que realizó la acción (si aplica)"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP"
    )

    class Meta:
        verbose_name = "Historial de Turno"
        verbose_name_plural = "Historial de Turnos"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.turno.codigo} - {self.accion} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class ReservaTemporal(models.Model):
    """
    Reserva temporal de un slot de turno.
    Se usa para evitar que dos usuarios seleccionen el mismo horario simultáneamente.
    Las reservas expiran después de un tiempo configurable (por defecto 10 minutos).
    """
    taller = models.ForeignKey(
        Taller,
        on_delete=models.CASCADE,
        verbose_name="Taller",
        related_name='reservas_temporales'
    )
    tipo_vehiculo = models.ForeignKey(
        TipoVehiculo,
        on_delete=models.CASCADE,
        verbose_name="Tipo de Vehículo"
    )
    fecha = models.DateField(verbose_name="Fecha del Turno")
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")

    # Identificador de sesión para vincular la reserva al usuario
    session_key = models.CharField(
        max_length=40,
        verbose_name="Clave de Sesión",
        help_text="Identificador único de la sesión del usuario"
    )

    # Control de expiración
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    expira_at = models.DateTimeField(
        verbose_name="Fecha de Expiración",
        help_text="Momento en que la reserva expira automáticamente"
    )

    class Meta:
        verbose_name = "Reserva Temporal"
        verbose_name_plural = "Reservas Temporales"
        # Una sesión solo puede tener una reserva activa por taller/tipo/fecha/hora
        unique_together = ['taller', 'tipo_vehiculo', 'fecha', 'hora_inicio', 'session_key']
        indexes = [
            models.Index(fields=['expira_at']),
            models.Index(fields=['session_key']),
            models.Index(fields=['taller', 'fecha', 'hora_inicio']),
        ]

    def __str__(self):
        return f"Reserva {self.taller.get_nombre()} - {self.fecha} {self.hora_inicio} (expira: {self.expira_at})"

    @property
    def esta_activa(self):
        """Verifica si la reserva aún está vigente"""
        return timezone.now() < self.expira_at

    @classmethod
    def limpiar_expiradas(cls):
        """Elimina todas las reservas expiradas"""
        return cls.objects.filter(expira_at__lt=timezone.now()).delete()

    @classmethod
    def contar_reservas_activas(cls, taller, tipo_vehiculo, fecha, hora_inicio, excluir_session=None):
        """
        Cuenta las reservas temporales activas para un slot específico.
        Opcionalmente excluye una sesión específica (la del usuario actual).
        """
        qs = cls.objects.filter(
            taller=taller,
            tipo_vehiculo=tipo_vehiculo,
            fecha=fecha,
            hora_inicio=hora_inicio,
            expira_at__gt=timezone.now()
        )
        if excluir_session:
            qs = qs.exclude(session_key=excluir_session)
        return qs.count()

    @classmethod
    def crear_o_actualizar(cls, taller, tipo_vehiculo, fecha, hora_inicio, session_key, minutos_expiracion=10):
        """
        Crea o actualiza una reserva temporal para un slot.
        Si ya existe una reserva de esta sesión, la actualiza.
        Si es un nuevo slot, elimina reservas anteriores de esta sesión.
        """
        from datetime import timedelta

        # Limpiar reservas expiradas primero
        cls.limpiar_expiradas()

        # Eliminar reservas anteriores de esta sesión (un usuario solo puede reservar un slot a la vez)
        cls.objects.filter(session_key=session_key).delete()

        # Crear nueva reserva
        expira_at = timezone.now() + timedelta(minutes=minutos_expiracion)

        return cls.objects.create(
            taller=taller,
            tipo_vehiculo=tipo_vehiculo,
            fecha=fecha,
            hora_inicio=hora_inicio,
            session_key=session_key,
            expira_at=expira_at
        )
