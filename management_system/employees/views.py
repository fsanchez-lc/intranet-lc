from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Empleado, Departamento # <--- 1. IMPORTAR DEPARTAMENTO
from django.contrib import messages
from .forms import EmpleadoForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string

# Función para verificar si es admin
def is_admin_check(user):
    return user.is_authenticated and user.groups.filter(name='Administrativo').exists()

@login_required
def EmployeesView(request):
    is_admin = request.user.groups.filter(name='Administrativo').exists()
    form_empleado = EmpleadoForm(prefix='create_empleado') 
    form_with_errors = None
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'empleado':
            form_empleado = EmpleadoForm(request.POST, request.FILES, prefix='create_empleado')             
            if form_empleado.is_valid():
                empleado_guardado = form_empleado.save()
                messages.success(request, f'¡Nuevo empleado "{empleado_guardado.nombre}" guardado exitosamente! 👍')                
                return redirect('employees:employees') 
            else:
                messages.error(request, 'Error al guardar el empleado. Revisa los campos.')
                form_with_errors = 'empleado'
        else:
                messages.error(request, 'Error desconocido al enviar el formulario.')
                form_empleado = EmpleadoForm(prefix='create_empleado')
    else:
        form_empleado = EmpleadoForm(prefix='create_empleado')
    
    # Obtenemos los filtros de la URL (si los hay)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('depto_id', '')

    # Filtro de búsqueda (igual que en BuscarDocumentosView)
    lookup = Q()
    if query:
        lookup = (
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(posicion__icontains=query) |
            Q(user__username__icontains=query, user__isnull=False) 
        )

    # Filtro de departamento
    depto_query = Q()
    if depto_id:
        depto_query = Q(departamento__id=depto_id)

    # Obtenemos la lista base de empleados ACTIVOS y aplicamos filtros
    empleados_activos = Empleado.objects.filter(
        lookup,
        depto_query,
        estado=Empleado.EstadoEmpleado.ACTIVO,
    ).distinct().order_by('nombre')

    paginator = Paginator(empleados_activos, 6) # 6 tarjetas por página
    page_number = request.GET.get('page', 1)
    empleados_page = paginator.get_page(page_number)

    empleados_list_full = Empleado.objects.all().order_by('nombre')
    all_departamentos = Departamento.objects.all().order_by('nombre')

    context = {
        'is_admin': is_admin,
        'form_with_errors': form_with_errors,
        'form_empleado': form_empleado,
        'empleados_page': empleados_page,
        'all_departamentos': all_departamentos,
        'current_q': query,
        'current_depto_id': depto_id,
        'todos_los_empleados': empleados_list_full,    
    }
    return render(request, 'employees.html', context)

@login_required
def SearchEmployeesView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('depto_id', '')

    lookup = Q()
    if query:
        lookup = (
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(posicion__icontains=query) |
            Q(user__username__icontains=query, user__isnull=False)
        )

    depto_query = Q()
    if depto_id:
        depto_query = Q(departamento__id=depto_id)

    empleados_activos = Empleado.objects.filter(
        lookup,
        depto_query,
        estado=Empleado.EstadoEmpleado.ACTIVO,
    ).distinct().order_by('nombre')

    paginator = Paginator(empleados_activos, 6) # Mismo número de página
    empleados_page = paginator.get_page(page_number)

    html = render_to_string(
         '_employee_cards.html', # <--- RUTA CORREGIDA
        {
            'empleados_page': empleados_page, 
            'is_admin': request.user.groups.filter(name='Administrativo').exists()
        }
    ) 

    return JsonResponse({
        'html': html,
        'has_next': empleados_page.has_next()
    })



@user_passes_test(is_admin_check)
def EditEmpleadoView(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
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