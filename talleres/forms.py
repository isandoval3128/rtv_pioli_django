from django import forms
from django.contrib import admin
from .models import Taller


class FechasNoLaborablesWidget(forms.Textarea):
    """Widget personalizado para gestionar fechas no laborables"""

    def __init__(self, attrs=None):
        default_attrs = {
            'rows': 5,
            'cols': 40,
            'placeholder': 'Ingresá las fechas en formato YYYY-MM-DD, una por línea.\nEjemplo:\n2024-12-25\n2025-01-01\n2025-05-01',
            'style': 'font-family: monospace;'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    class Media:
        css = {
            'all': ('admin/css/fechas_no_laborables.css',)
        }
        js = ('admin/js/fechas_no_laborables.js',)


class TallerAdminForm(forms.ModelForm):
    """Form personalizado para el admin de Taller"""

    fechas_no_laborables_text = forms.CharField(
        widget=FechasNoLaborablesWidget(),
        required=False,
        label='Fechas No Laborables',
        help_text='Ingresá cada fecha en una línea nueva, en formato YYYY-MM-DD (Ej: 2024-12-25)'
    )

    class Meta:
        model = Taller
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Convertir el JSON a texto para mostrar en el textarea
        if self.instance and self.instance.pk and self.instance.fechas_no_laborables:
            fechas = self.instance.fechas_no_laborables
            if isinstance(fechas, list):
                self.initial['fechas_no_laborables_text'] = '\n'.join(fechas)

    def clean_fechas_no_laborables_text(self):
        """Validar y procesar las fechas ingresadas"""
        from datetime import datetime

        text = self.cleaned_data.get('fechas_no_laborables_text', '')
        if not text.strip():
            return []

        fechas = []
        errores = []

        for line_num, line in enumerate(text.strip().split('\n'), 1):
            line = line.strip()
            if not line:  # Saltar líneas vacías
                continue

            try:
                # Validar formato de fecha
                fecha = datetime.strptime(line, '%Y-%m-%d')
                fecha_str = fecha.strftime('%Y-%m-%d')

                if fecha_str not in fechas:
                    fechas.append(fecha_str)
            except ValueError:
                errores.append(f'Línea {line_num}: "{line}" no es una fecha válida (use formato YYYY-MM-DD)')

        if errores:
            raise forms.ValidationError('\n'.join(errores))

        # Ordenar fechas
        fechas.sort()
        return fechas

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Guardar las fechas procesadas en el campo JSON
        instance.fechas_no_laborables = self.cleaned_data.get('fechas_no_laborables_text', [])

        if commit:
            instance.save()

        return instance
