from django import forms
from .models import Curso, Documento
from employees.models import Empleado, Departamento
from django.core.exceptions import ValidationError

class CursoForm(forms.ModelForm):

    class Meta:
        model = Curso
        fields = [
            'titulo', 'descripcion', 'fecha', 'horario', 'duracion_horas',
            'plataforma', 'link', 'imagen', 'estado', 'es_general',
            'departamentos_destinados', 'inscritos'
        ]

        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # Estos inputs ya son compatibles con Bootstrap
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'horario': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duracion_horas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            
            'plataforma': forms.TextInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            
            'estado': forms.Select(attrs={'class': 'form-select'}),

            # Checkbox usa una clase diferente
            'es_general': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            'departamentos_destinados': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'data-placeholder': 'Busca y selecciona departamentos'
            }),
            'inscritos': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'data-placeholder': 'Busca y selecciona empleados'
            }),
        }
        
        labels = {
            'titulo': 'Título del curso',
            'es_general': '¿Es un curso general (para todos)?',
            'departamentos_destinados': 'Departamentos específicos',
            'inscritos': 'Inscribir empleados',
        }

    # Para que los campos ManyToMany se muestren correctamente
    # (Django los inicializa vacíos por defecto)
    def __init__(self, *args, **kwargs):
        super(CursoForm, self).__init__(*args, **kwargs)
        self.fields['departamentos_destinados'].queryset = Departamento.objects.all()
        self.fields['inscritos'].queryset = Empleado.objects.all().order_by('nombre')

class DocumentoForm(forms.ModelForm):
    
    # Override para inicializar con Select2
    departamentos_destinados = forms.ModelMultipleChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-select', 
                'data-placeholder': 'Selecciona uno o más departamentos'
            }
        ),
        label="Departamentos Destinados", # El modelo ya tiene un verbose_name, pero lo ponemos para asegurar
        help_text="Departamentos que pueden ver esto (si no es 'general')."
    )

    class Meta:
        model = Documento
        
        # Campos que el usuario llenará
        fields = [
            'nombre', 'descripcion', 'codigo_documento', 'tipo_documento',
            'archivo', 'enlace_externo', 'palabras_clave', 'estado', 
            'es_general', 'departamentos_destinados'
        ]
        
        # Aplicar clases de Bootstrap a todos los campos
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'codigo_documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. RRHH-FOR-001'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'enlace_externo': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'palabras_clave': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. vacaciones, permiso, solicitud'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'es_general': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_es_general_doc'}), # ID único
        }

    def clean(self):
        # Llama al método clean() padre para obtener los datos limpios
        cleaned_data = super().clean()
        
        # Obtenemos los valores de los campos
        archivo = cleaned_data.get("archivo")
        enlace_externo = cleaned_data.get("enlace_externo")

        # Comprobamos nuestra lógica
        if not archivo and not enlace_externo:
            # Si AMBOS están vacíos, lanzamos un error
            raise ValidationError(
                "Debes proporcionar al menos un Archivo o un Enlace Externo.",
                code='archivo_o_enlace_requerido'
            )
        
        # Si al menos uno tiene valor, la validación es correcta
        return cleaned_data