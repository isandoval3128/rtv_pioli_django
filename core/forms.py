from django import forms
from .models import Service, PortfolioItem, TimelineEvent, TeamMember, ContactMessage, SiteConfiguration


class ServiceForm(forms.ModelForm):
    """Form para el modelo Service"""
    class Meta:
        model = Service
        fields = ['icon', 'title', 'description', 'order', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class PortfolioItemForm(forms.ModelForm):
    """Form para el modelo PortfolioItem"""
    class Meta:
        model = PortfolioItem
        fields = ['title', 'subtitle', 'thumbnail', 'full_image', 'description',
                 'client', 'category', 'order', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class TimelineEventForm(forms.ModelForm):
    """Form para el modelo TimelineEvent"""
    class Meta:
        model = TimelineEvent
        fields = ['date', 'title', 'description', 'image', 'order',
                 'inverted', 'is_final', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class TeamMemberForm(forms.ModelForm):
    """Form para el modelo TeamMember"""
    class Meta:
        model = TeamMember
        fields = ['name', 'position', 'photo', 'twitter_url', 'facebook_url',
                 'linkedin_url', 'order', 'active']


class ContactForm(forms.ModelForm):
    """Form público para contacto con validaciones"""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu Nombre *',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu Email *',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu Teléfono *',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tu Mensaje *',
                'required': True,
                'rows': 5,
            }),
        }

    def clean_email(self):
        """Validación adicional para email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email

    def clean_phone(self):
        """Validación adicional para teléfono"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Eliminar espacios y caracteres especiales
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 8:
                raise forms.ValidationError('El teléfono debe tener al menos 8 dígitos')
        return phone

    def clean_message(self):
        """Validación adicional para mensaje"""
        message = self.cleaned_data.get('message')
        if message and len(message) < 10:
            raise forms.ValidationError('El mensaje debe tener al menos 10 caracteres')
        return message


class SiteConfigurationForm(forms.ModelForm):
    """Form para el modelo SiteConfiguration"""
    class Meta:
        model = SiteConfiguration
        fields = [
            'site_title', 'site_logo', 'hero_title', 'hero_subtitle', 'hero_button_text',
            'footer_copyright', 'twitter_url', 'facebook_url', 'linkedin_url',
            'contact_email', 'contact_phone', 'contact_address',
            'primary_color', 'secondary_color', 'font_family',
            'base_font_size', 'heading_font_size_h1', 'heading_font_size_h2',
            'heading_font_size_h3', 'heading_font_size_h4'
        ]
        widgets = {
            'contact_address': forms.Textarea(attrs={'rows': 3}),
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
        }

    def clean_primary_color(self):
        """Validación para color primario"""
        color = self.cleaned_data.get('primary_color')
        if color and not color.startswith('#'):
            color = f'#{color}'
        if len(color) != 7:
            raise forms.ValidationError('El color debe estar en formato hexadecimal (#RRGGBB)')
        return color

    def clean_secondary_color(self):
        """Validación para color secundario"""
        color = self.cleaned_data.get('secondary_color')
        if color and not color.startswith('#'):
            color = f'#{color}'
        if len(color) != 7:
            raise forms.ValidationError('El color debe estar en formato hexadecimal (#RRGGBB)')
        return color
