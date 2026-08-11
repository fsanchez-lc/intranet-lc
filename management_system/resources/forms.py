from django import forms
from .models import Curso, Documento, VideoCurso, Slide
from employees.models import Empleado, Departamento
from .models import TipoDocumento, Documento

from django.core.exceptions import ValidationError

class SlideForm(forms.ModelForm):
    class Meta:
        model = Slide
        fields = ['title', 'description', 'image', 'alt_text', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del slide'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción (opcional)'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto alternativo para accesibilidad'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Título Principal',
        }

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = [
            'titulo', 'descripcion', 'fecha', 'horario', 'duracion_horas',
            'plataforma', 'link', 'imagen', 'estado', 'modalidad', 'es_general',
            'departamentos_destinados', 'inscritos'
        ]

        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'horario': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duracion_horas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'plataforma': forms.TextInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'modalidad': forms.Select(attrs={'class': 'form-select'}),
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
            'modalidad': 'Modalidad de Inscripción',
            'es_general': '¿Es un curso general (para todos)?',
            'departamentos_destinados': 'Departamentos específicos',
            'inscritos': 'Inscribir empleados',
        }

    def __init__(self, *args, **kwargs):
        super(CursoForm, self).__init__(*args, **kwargs)
        self.fields['departamentos_destinados'].queryset = Departamento.objects.all()
        self.fields['inscritos'].queryset = Empleado.objects.all().order_by('nombre')
        if self.instance and self.instance.fecha:
            self.initial['fecha'] = self.instance.fecha.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        es_general = cleaned_data.get('es_general')
        departamentos = cleaned_data.get('departamentos_destinados')

        if not es_general and not departamentos:
            self.add_error('departamentos_destinados', 
                            "Si el curso NO es 'General', debes seleccionar al menos un departamento.")
        return cleaned_data

class DocumentoForm(forms.ModelForm):
    departamentos_destinados = forms.ModelMultipleChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-select', 
                'data-placeholder': 'Selecciona uno o más departamentos'
            }
        ),
        label="Departamentos Destinados",
        help_text="Departamentos que pueden ver esto (si no es 'general')."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Definir los grupos
        choices = [('', '---------')] # Opción por defecto
        
        # Obtenemos los QuerySets
        # Nota: Ajusta los filtros según cómo identifiques internos de externos en tu DB
        internos = TipoDocumento.objects.filter(categoria='interno').values_list('id', 'nombre')
        externos = TipoDocumento.objects.filter(categoria='externo').values_list('id', 'nombre')
        
        # Construimos la lista con optgroups (Django lo reconoce por ser una lista de tuplas anidadas)
        grouped_choices = [('', '---------')]
        
        if internos.exists():
            grouped_choices.append(('Documentación Interna', list(internos)))
        
        if externos.exists():
            grouped_choices.append(('Marco Normativo / Externo', list(externos)))
            
        # 2. Asignamos las nuevas opciones al widget
        self.fields['tipo_documento'].choices = grouped_choices

    class Meta:
        model = Documento
        fields = [
            'nombre', 'descripcion', 'codigo_documento', 'tipo_documento', 'procedimiento',
            'archivo', 'enlace_externo', 'palabras_clave', 'estado', 
            'es_general', 'departamentos_destinados'
        ]
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'codigo_documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. RRHH-FOR-001'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'procedimiento': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'enlace_externo': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'palabras_clave': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. vacaciones, permiso, solicitud'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'es_general': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_es_general_doc'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        archivo = cleaned_data.get("archivo")
        enlace_externo = cleaned_data.get("enlace_externo")
        es_general = cleaned_data.get('es_general')
        departamentos = cleaned_data.get('departamentos_destinados')

        if not archivo and not enlace_externo:
            raise ValidationError(
                "Debes proporcionar al menos un Archivo o un Enlace Externo.",
                code='archivo_o_enlace_requerido'
            )
        
        es_general = cleaned_data.get('es_general')
        departamentos = cleaned_data.get('departamentos_destinados')

        if not es_general and not departamentos:
            self.add_error('departamentos_destinados', 
                           "Si el documento NO es 'General', debes seleccionar al menos un departamento.")
            
        return cleaned_data
    
class VideoCursoForm(forms.ModelForm):
    class Meta:
        model = VideoCurso
        fields = [
            'titulo', 
            'video_url', 
            'ponente', 
            'fecha_grabacion', 
            'tematica',
            'curso', 
            'estado', 
            'es_general', 
            'departamentos_destinados'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'ponente': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_grabacion': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'tematica': forms.Select(attrs={'class': 'form-select'}),
            'curso': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'es_general': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'departamentos_destinados': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }
        labels = {
            'tematica': 'Temática del Contenido',
            'video_url': 'URL del Video',
            'fecha_grabacion': 'Fecha de Grabación',
            'es_general': 'Contenido General',
            'departamentos_destinados': 'Departamentos Destinados (si no es general)',
        }
    def __init__(self, *args, **kwargs):
        super(VideoCursoForm, self).__init__(*args, **kwargs)
        self.fields['departamentos_destinados'].queryset = Departamento.objects.all()

        if self.instance and self.instance.fecha_grabacion:
            self.initial['fecha_grabacion'] = self.instance.fecha_grabacion.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        es_general = cleaned_data.get('es_general')
        departamentos = cleaned_data.get('departamentos_destinados')

        if not es_general and not departamentos:
            self.add_error('departamentos_destinados', 
                           "Si el video NO es 'General', debes seleccionar al menos un departamento.")
        return cleaned_data