from django.shortcuts import render, redirect
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from .models import Empleado, Departamento, Permiso
from django.contrib import messages
from .forms import EmpleadoForm # Importa el nuevo formulario
from django.core.paginator import Paginator # Importa el Paginador

@login_required
def EmployeesView(request):
    is_admin = request.user.groups.filter(name='Administrativo').exists()

    if 'crear_empleado_form' in request.session:
        # Recupera el formulario con errores de la sesión (si existe)
        form = request.session.pop('crear_empleado_form')
    else:
        # Si no, crea un formulario nuevo y vacío
        form = EmpleadoForm()

    empleados_list = Empleado.objects.all().order_by('nombre')
    
    # Muestra 10 empleados por página
    paginator = Paginator(empleados_list, 10) 
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number) # page_obj se usará en la plantilla

    context = {
        'is_admin': is_admin,
        'page_obj': page_obj,
        'crear_empleado_form': form, # Pasa el formulario al contexto
        # 'empleados': empleados_list,
    }
    return render(request, 'employees.html', context)

@login_required
def CrearEmpleadoView(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, '¡Empleado creado exitosamente!')
        else:
            # Si el formulario NO es válido
            messages.error(request, 'Hubo un error. Por favor corrige el formulario.')
            # Guarda el formulario con errores en la sesión para mostrarlo
            request.session['crear_empleado_form'] = form.as_p() # O una forma de pasarlo
            
            # --- Corrección importante ---
            # En lugar de guardar en sesión, es mejor re-renderizar la vista
            # que muestra el modal, pasándole el formulario con errores.
            
            empleados_list = Empleado.objects.all().order_by('nombre')
            paginator = Paginator(empleados_list, 10)
            page_obj = paginator.get_page(request.GET.get('page'))
            
            context = {
                'page_obj': page_obj,
                'crear_empleado_form': form # Pasa el formulario CON errores
            }
            # Vuelve a renderizar la página de la lista, el modal mostrará los errores
            return render(request, 'employees/tu_plantilla_de_empleados.html', context)

    # Redirige de vuelta a la lista (a la página 1)
    return redirect('employees:employees')