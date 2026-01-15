from django import forms
from django.core.exceptions import ValidationError
from clientes.models import Cliente
from territorios.models import Localidad
from talleres.models import Vehiculo, TipoVehiculo, Taller
from .models import Turno
import re


class Step1ClienteForm(forms.Form):
    """Paso 1: Búsqueda o creación de cliente"""

    # Búsqueda
    dni_busqueda = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese DNI',
            'id': 'dni_busqueda'
        }),
        label='DNI del Cliente'
    )

    # Creación de nuevo cliente
    dni = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'data-cleave': 'dni'
        }),
        label='DNI'
    )

    nombre = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del cliente'
        }),
        label='Nombre'
    )

    apellido = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido del cliente'
        }),
        label='Apellido'
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@ejemplo.com'
        }),
        label='Email'
    )

    cel = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3884123456',
            'data-cleave': 'phone'
        }),
        label='Celular'
    )

    localidad = forms.ModelChoiceField(
        queryset=Localidad.objects.all().order_by('departamento__nombre', 'nombre'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Localidad'
    )

    domicilio = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección completa'
        }),
        label='Domicilio'
    )

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni and not dni.isdigit():
            raise ValidationError('El DNI debe contener solo números')
        if dni and len(dni) < 7:
            raise ValidationError('El DNI debe tener al menos 7 dígitos')
        return dni


class Step2VehiculoForm(forms.Form):
    """Paso 2: Datos del vehículo"""

    # Búsqueda
    dominio_busqueda = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'ABC123 o AB123CD',
            'id': 'dominio_busqueda',
            'data-cleave': 'plate'
        }),
        label='Dominio del Vehículo'
    )

    # Creación
    dominio = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'ABC123 o AB123CD',
            'data-cleave': 'plate'
        }),
        label='Dominio'
    )

    tipo_vehiculo = forms.ModelChoiceField(
        queryset=TipoVehiculo.objects.filter(status=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Trámite RTO'
    )

    tiene_gnc = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='¿Tiene GNC?'
    )

    def clean_dominio(self):
        dominio = self.cleaned_data.get('dominio', '').upper().replace(' ', '')

        # Validar formatos válidos de patente argentina
        patron_viejo = r'^[A-Z]{3}\d{3}$'  # ABC123
        patron_nuevo = r'^[A-Z]{2}\d{3}[A-Z]{2}$'  # AB123CD

        if dominio and not (re.match(patron_viejo, dominio) or re.match(patron_nuevo, dominio)):
            raise ValidationError('Formato de dominio inválido. Use ABC123 o AB123CD')

        return dominio


class Step3TallerForm(forms.Form):
    """Paso 3: Selección de taller"""

    taller = forms.ModelChoiceField(
        queryset=Taller.objects.filter(status=True),
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Seleccione un taller'
    )


class Step4FechaHoraForm(forms.Form):
    """Paso 4: Selección de fecha y hora"""

    fecha = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'datepicker',
            'placeholder': 'Seleccione una fecha',
            'readonly': 'readonly'
        }),
        label='Fecha del turno'
    )

    hora_inicio = forms.TimeField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'horario_select'
        }),
        label='Horario disponible'
    )

    def __init__(self, *args, **kwargs):
        # Recibir horarios disponibles como parámetro
        horarios_disponibles = kwargs.pop('horarios_disponibles', [])
        super().__init__(*args, **kwargs)

        # Crear choices dinámicamente
        if horarios_disponibles:
            choices = [(h, h.strftime('%H:%M')) for h in horarios_disponibles]
            self.fields['hora_inicio'].widget = forms.Select(
                choices=choices,
                attrs={'class': 'form-select', 'id': 'horario_select'}
            )


class Step5ConfirmacionForm(forms.Form):
    """Paso 5: Confirmación final"""

    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones o comentarios adicionales (opcional)'
        }),
        label='Observaciones'
    )

    acepta_terminos = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Acepto los términos y condiciones',
        error_messages={
            'required': 'Debe aceptar los términos y condiciones para continuar'
        }
    )

    recaptcha_token = forms.CharField(
        required=True,
        widget=forms.HiddenInput(attrs={
            'id': 'recaptcha_token'
        })
    )


class CancelarTurnoForm(forms.Form):
    """Formulario para cancelar un turno"""

    token = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo de la cancelación (opcional)'
        }),
        label='Motivo de cancelación'
    )


class BuscarTurnoForm(forms.Form):
    """Formulario para buscar un turno"""

    TIPO_BUSQUEDA = [
        ('codigo', 'Código de turno'),
        ('dominio', 'Dominio del vehículo'),
        ('dni', 'DNI del cliente'),
    ]

    tipo_busqueda = forms.ChoiceField(
        choices=TIPO_BUSQUEDA,
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Buscar por',
        initial='codigo'
    )

    valor_busqueda = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el valor a buscar',
            'id': 'valor_busqueda'
        }),
        label='Valor'
    )
