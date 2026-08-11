from django import forms
from django.contrib.auth.models import Group
from .models import Empleado, Departamento, Vacacion
from service_stations.models import ServiceStation 
from django.contrib.auth import get_user_model

User = get_user_model()

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            # 1. Información Personal / Identificación
            'numero_empleado', 'nombre', 'sexo', 'fecha_nacimiento', 'foto',
            
            # 2. Contacto
            'email', 'telefono', 'telefono_emergencia',
            
            # 3. Laboral
            'fecha_ingreso', 'departamento', 'posicion', 'estacion_servicio', 'estado',
            
            # 4. Sistema y Autenticación
            'user', 'grupos', 'firma_digital'
        ]

        widgets = {
            'numero_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_nacimiento': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),

            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            
            'fecha_ingreso': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'posicion': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'estacion_servicio': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),

            'user': forms.Select(attrs={'class': 'form-select'}),
            'grupos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'firma_digital': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lógica para mostrar solo usuarios libres o el actual
        usuarios_libres = User.objects.filter(empleado__isnull=True)
        if self.instance and self.instance.user:
            usuario_actual = User.objects.filter(pk=self.instance.user.pk)
            self.fields['user'].queryset = (usuarios_libres | usuario_actual).distinct()
            self.fields['grupos'].initial = self.instance.user.groups.all()
        else:
            self.fields['user'].queryset = usuarios_libres
            
        self.fields['departamento'].queryset = Departamento.objects.all()
        self.fields['estacion_servicio'].queryset = ServiceStation.objects.all()
        self.fields['grupos'].queryset = Group.objects.all()

        # Campos opcionales (Asegurando que coincidan con tu modelo null=True, blank=True)
        self.fields['foto'].required = False
        self.fields['telefono'].required = False
        self.fields['telefono_emergencia'].required = False
        
        self.fields['user'].required = False
        self.fields['departamento'].required = False
        self.fields['estacion_servicio'].required = False
        self.fields['firma_digital'].required = False
        self.fields['grupos'].required = False

    def save(self, commit=True):
        # 1. Guardamos la instancia del Empleado primero
        empleado = super().save(commit=False)

        if commit:
            empleado.save()
            # Guardamos las relaciones ManyToMany del propio modelo Empleado
            self.save_m2m() 

            # Verificamos si el empleado tiene un usuario vinculado
            if empleado.user:
                # Obtenemos los grupos seleccionados en el formulario
                grupos_seleccionados = self.cleaned_data.get('grupos')
                
                if grupos_seleccionados is not None:
                    empleado.user.groups.set(grupos_seleccionados)
                    empleado.user.save()
        
        return empleado
    
class VacacionForm(forms.ModelForm):
    class Meta:
        model = Vacacion
        fields = [
            'empleado', 'dias_seleccionados', 'autorizador', 
            'archivo_vacaciones', 'archivo_roles', 'estado', 'observaciones'
        ]
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            
            # 2. Este campo ahora es un HiddenInput porque se llena mediante el Script de FullCalendar
            'dias_seleccionados': forms.HiddenInput(),
            
            'autorizador': forms.Select(attrs={'class': 'form-select'}),
            
            'estado': forms.Select(attrs={'class': 'form-select'}),
            
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe notas adicionales aquí...'
            }),
            
            # Los campos de archivo usan form-control para el estilo de Bootstrap
            'archivo_vacaciones': forms.FileInput(attrs={'class': 'form-control'}),
            'archivo_roles': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos para que solo aparezcan empleados activos
        self.fields['empleado'].queryset = Empleado.objects.filter(estado='ACTIVO')
        self.fields['autorizador'].queryset = Empleado.objects.filter(estado='ACTIVO')