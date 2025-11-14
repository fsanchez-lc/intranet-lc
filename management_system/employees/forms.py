# employees/forms.py
from django import forms
from django.contrib.auth.models import Group, User
from .models import Empleado, Departamento, Permiso
from service_stations.models import ServiceStation 

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'email', 'telefono', 'posicion',
            'user', 'departamento', 'estacion_servicio', 'estado',
            'grupos', 'politicas_permisos', 'firma_digital'
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'posicion': forms.TextInput(attrs={'class': 'form-control'}),

            'user': forms.Select(attrs={'class': 'form-select'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'estacion_servicio': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),

            'grupos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'politicas_permisos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),

            'firma_digital': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        # ... tu __init__ está perfecto, no lo cambies ...
        super().__init__(*args, **kwargs)        
        # Obtenemos todos los usuarios que aún NO están ligados a un empleado
        usuarios_libres = User.objects.filter(empleado__isnull=True)
        if self.instance and self.instance.user:
            usuario_actual = User.objects.filter(pk=self.instance.user.pk)
            self.fields['user'].queryset = (usuarios_libres | usuario_actual).distinct()
        else:
            self.fields['user'].queryset = usuarios_libres        
        self.fields['departamento'].queryset = Departamento.objects.all()
        self.fields['estacion_servicio'].queryset = ServiceStation.objects.all()
        self.fields['grupos'].queryset = Group.objects.all()
        self.fields['politicas_permisos'].queryset = Permiso.objects.all()

        # Hacemos los campos no-requeridos en el modelo, también no-requeridos en el form
        self.fields['user'].required = False
        self.fields['departamento'].required = False
        self.fields['estacion_servicio'].required = False
        self.fields['telefono'].required = False
        self.fields['posicion'].required = False
        self.fields['firma_digital'].required = False