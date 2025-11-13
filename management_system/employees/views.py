from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Empleado
from django.contrib import messages
from .forms import EmpleadoForm

# Función para verificar si es admin
def is_admin_check(user):
    return user.is_authenticated and user.groups.filter(name='Administrativo').exists()

@login_required
def EmployeesView(request):
    is_admin = request.user.groups.filter(name='Administrativo').exists()

    form_empleado = EmpleadoForm(prefix='create_empleado') 

    form_with_errors = None
    if request.method == 'POST':
        # Identificamos qué formulario se envió
        form_type = request.POST.get('form_type')

        if form_type == 'empleado':
            form_empleado = EmpleadoForm(request.POST, request.FILES, prefix='create_empleado')         

            if form_empleado.is_valid():
                empleado_guardado = form_empleado.save() # Guardamos la instancia
                messages.success(request, f'¡Nuevo empleado "{empleado_guardado.nombre}" guardado exitosamente! 👍')                
                return redirect('employees:employees') 
            else:
                messages.error(request, 'Error al guardar el empleado. Revisa los campos.')
                form_with_errors = 'empleado'
        else:
                # Fallback por si no se identifica el form
                messages.error(request, 'Error desconocido al enviar el formulario.')
                form_empleado = EmpleadoForm(prefix='create_empleado')
    else:
        form_empleado = EmpleadoForm(prefix='create_empleado')

    empleados_list = Empleado.objects.all().order_by('nombre')

    context = {
        'is_admin': is_admin,
        'form_with_errors': form_with_errors,
        'form_empleado': form_empleado,
        'todos_los_empleados': empleados_list,
    }
    return render(request, 'employees.html', context)

# Edu
@user_passes_test(is_admin_check)
def EditEmpleadoView(request, empleado_id):
    """
    Maneja el GET (cargar formulario parcial) y POST (actualizar)
    para el modal de edición de empleados.
    """
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        # El usuario está enviando el formulario actualizado
        form = EmpleadoForm(request.POST, request.FILES, instance=empleado, prefix="edit-empleado")
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Empleado "{empleado.nombre}" actualizado con éxito.')
            return redirect('employees:employees')
        else:
            messages.error(request, 'Error al actualizar el documento. Revisa los campos.')
            pass 

    else:
        # El usuario está pidiendo el formulario por primera vez (AJAX/Fetch)
        form = EmpleadoForm(instance=empleado, prefix="edit-empleado")
    
    # Para GET o POST fallido, renderizamos el formulario parcial
    return render(request, '_edit_empleado_form.html', {
        'form_empleado_edit': form,
        'empleado': empleado
    })