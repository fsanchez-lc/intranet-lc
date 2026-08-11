from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateWidget
from django.contrib.auth.models import User, Group
from .models import Empleado, Departamento
# Importa ServiceStation desde su app correspondiente
from service_stations.models import ServiceStation 

class EmpleadoResource(resources.ModelResource):
    # 1. Mapeamos el Usuario (User) por su 'username'
    user = fields.Field(
        column_name='usuario',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )

    # 2. Mapeamos el Departamento por su 'nombre'
    departamento = fields.Field(
        column_name='departamento',
        attribute='departamento',
        widget=ForeignKeyWidget(Departamento, 'nombre')
    )

    # 3. Mapeamos el Centro de Trabajo (ServiceStation) por su 'nombre'
    estacion_servicio = fields.Field(
        column_name='estacion_servicio',
        attribute='estacion_servicio',
        widget=ForeignKeyWidget(ServiceStation, 'nombre') # Ajusta 'name' al campo real de ServiceStation
    )

    # 4. Para los Grupos (ManyToMany), usamos comas para separar varios grupos en el Excel
    grupos = fields.Field(
        column_name='grupos',
        attribute='grupos',
        widget=ManyToManyWidget(Group, separator=',', field='name')
    )

    fecha_ingreso = fields.Field(
        column_name='fecha_ingreso',
        attribute='fecha_ingreso',
        widget=DateWidget(format='%d/%m/%Y') # Para fechas tipo 16/02/2026
    )

    # Configuramos el formato para fecha_nacimiento
    fecha_nacimiento = fields.Field(
        column_name='fecha_nacimiento',
        attribute='fecha_nacimiento',
        widget=DateWidget(format='%d/%m/%Y')
    )

    class Meta:
        model = Empleado
        # Definimos el orden y los campos que queremos en el Excel
        fields = (
            'numero_empleado', 'grupos', 'nombre', 'email', 'estado', 'sexo', 'departamento', 'user',
            'posicion', 'estacion_servicio', 'fecha_ingreso', 'fecha_nacimiento', 'telefono_emergencia'
        )
        
        # Usamos el email como llave única para actualizar datos si el empleado ya existe
        import_id_fields = ['email']
        # Evita que se creen registros vacíos
        skip_unchanged = True
        report_skipped = True
    
    def after_save_instance(self, instance, *args, **kwargs):
        """
        Este método se ejecuta después de guardar el empleado.
        Aquí forzamos que pertenezca al grupo 'Empleado'.
        """
        dry_run = kwargs.get('dry_run', False)
        
        if not dry_run:
            # Buscamos o creamos el grupo 'Empleado'
            grupo_empleado, created = Group.objects.get_or_create(name='Empleado')
            
            # Lo asignamos al empleado
            instance.grupos.add(grupo_empleado)