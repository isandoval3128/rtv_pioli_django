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
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese DNI o CUIL',
            'id': 'dni_busqueda'
        }),
        label='DNI / CUIL del Cliente'
    )

    # Creación de nuevo cliente
    dni = forms.CharField(
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678 o 20123456789',
            'data-cleave': 'dni'
        }),
        label='DNI / CUIL'
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
        if not dni:
            return dni
        if not dni.isdigit():
            raise ValidationError('Solo se permiten números, sin puntos ni guiones')
        if len(dni) <= 8:
            if len(dni) < 7:
                raise ValidationError('El DNI debe tener al menos 7 dígitos')
        elif len(dni) == 11:
            if not self._validar_cuil(dni):
                raise ValidationError('El CUIL ingresado no es válido')
        else:
            raise ValidationError('Ingrese un DNI (7-8 dígitos) o CUIL (11 dígitos)')
        return dni

    @staticmethod
    def _validar_cuil(cuil):
        """Valida un CUIL/CUIT argentino con el algoritmo de dígito verificador"""
        if len(cuil) != 11 or not cuil.isdigit():
            return False
        pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(cuil[i]) * pesos[i] for i in range(10))
        resto = 11 - (suma % 11)
        if resto == 11:
            digito = 0
        elif resto == 10:
            digito = 9
        else:
            digito = resto
        return int(cuil[10]) == digito


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

        if dominio:
            # Formatos válidos de patente argentina
            patrones = [
                r'^[A-Z]{3}\d{3}$',        # Auto viejo: ABC123
                r'^[A-Z]{2}\d{3}[A-Z]{2}$', # Auto nuevo Mercosur: AB123CD
                r'^[A-Z]\d{3}[A-Z]{3}$',    # Moto nueva Mercosur: A123BCD
                r'^\d{3}[A-Z]{3}$',          # Moto vieja: 123ABC
            ]
            if not any(re.match(p, dominio) for p in patrones):
                raise ValidationError('Formato de dominio inválido. Formatos válidos: ABC123, AB123CD, A123BCD, 123ABC')

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
        ('dni', 'DNI / CUIL del cliente'),
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
