from django.contrib import admin
from .models import Empleado, Departamento, Permiso

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    # --- CAMBIO AQUÍ: Añadido 'estacion_servicio' a la lista ---
    list_display = ('nombre', 'email', 'departamento', 'estacion_servicio', 'estado')
    
    # --- CAMBIO AQUÍ: Añadida la búsqueda por nombre de estación ---
    search_fields = ('nombre', 'email', 'departamento__nombre', 'estacion_servicio__nombre')
    
    # --- CAMBIO AQUÍ: Añadido el filtro por estación ---
    list_filter = ('estado', 'departamento', 'grupos', 'estacion_servicio')
    
    filter_horizontal = ('grupos', 'politicas_permisos')

    fieldsets = (
        ('Información Personal', {
            # --- CAMBIO AQUÍ: Añadido 'estacion_servicio' al formulario ---
            'fields': ('nombre', 'email','telefono', 'posicion', 'departamento', 'estacion_servicio', 'firma_digital')
        }),
        ('Estado, Tipos de Usuario y Permisos', {
            'fields': ('estado', 'grupos', 'politicas_permisos')
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        Sobrescribe el método save para asegurar que la contraseña
        siempre se guarde hasheada cuando se edita desde el admin.
        """
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        
        super().save_model(request, obj, form, change)

