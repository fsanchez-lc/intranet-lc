from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

class UsuarioForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User

        fields = ('username', 'email', 'first_name', 'last_name', 'groups')
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}), 
            'groups': forms.CheckboxSelectMultiple(),        
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

        self.fields['groups'].label = "Rol / Tipo de Usuario"


class UsuarioEditForm(UserChangeForm):
    password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,  # Permite dejar vacío para no cambiar
        help_text='Deja vacío para mantener la contraseña actual.'
    )
    password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active','groups')

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password and password != password2:
            raise forms.ValidationError("Las nuevas contraseñas no coinciden.")
        
        # Si una está vacía pero la otra no, también es error
        if (password and not password2) or (not password and password2):
             raise forms.ValidationError("Debes proporcionar y confirmar la nueva contraseña, o dejar ambos campos vacíos.")

        return cleaned_data
    
    # 4. Sobrescribir save() para manejar el cambio de contraseña
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        
        if password:
            # Solo si se proporcionó una nueva contraseña, la establecemos
            user.set_password(password)
        
        if commit:
            user.save()
            self.save_m2m() # Necesario para guardar grupos y permisos
        return user
