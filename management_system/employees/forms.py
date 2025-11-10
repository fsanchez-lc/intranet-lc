# employees/forms.py
from django import forms
from django.contrib.auth.models import Group, User
from .models import Empleado, Departamento, Permiso
# Asumo que ServiceStation está en 'service_stations.models'
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
            # Campos de texto y email
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'id_email'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_telefono'}),
            'posicion': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_posicion'}),

            # Selects (ForeignKey)
            'user': forms.Select(attrs={'class': 'form-select', 'id': 'id_user'}),
            'departamento': forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento'}),
            'estacion_servicio': forms.Select(attrs={'class': 'form-select', 'id': 'id_estacion_servicio'}),
            'estado': forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'}),

            # Checkboxes (ManyToMany) - Renderizará como checkboxes
            'grupos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'politicas_permisos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),

            # Archivo
            'firma_digital': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_firma_digital'}),
        }
        
    def __init__(self, *args, **kwargs):
        """
        Poblamos los QuerySets de los campos ForeignKey y ManyToMany.
        """
        super().__init__(*args, **kwargs)
        
        # Obtenemos todos los usuarios que aún NO están ligados a un empleado
        usuarios_libres = User.objects.filter(empleado__isnull=True)
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