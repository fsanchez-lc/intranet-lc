from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from service_stations.models import ServiceStation
from employees.models import Departamento, Empleado
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from .forms import UsuarioForm, UsuarioEditForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.models import Group
from navigation.decorators import validar_acceso_menu

User = get_user_model()

def is_admin_check(user):
    return user.is_authenticated and user.groups.filter(name='Administrador').exists()

@login_required
@validar_acceso_menu
def UsersView(request):
    is_admin = request.user.groups.filter(name='Administrador').exists()

    form_usuario = UsuarioForm(prefix='create_usuario') 
    form_with_errors = None
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'usuario':
            form_usuario = UsuarioForm(request.POST, request.FILES, prefix='create_usuario') 
            
            if form_usuario.is_valid():
                usuario_guardado = form_usuario.save(commit=False)
                usuario_guardado.save()
                form_usuario.save_m2m()           
                messages.success(request, f'¡Nuevo usuario "{usuario_guardado.username}" guardado exitosamente! 👍') 
                return redirect('users:users') 
            else:
                for field, errors in form_usuario.errors.items():
                    print(f"  - Campo '{field}': {errors}")

                messages.error(request, 'Error al guardar el usuario. Revisa los campos.')
                form_with_errors = 'usuario'
        else:
            messages.error(request, 'Error desconocido al enviar el formulario.')
            form_usuario = UsuarioForm(prefix='create_usuario')
    else:
        form_usuario = UsuarioForm(prefix='create_usuario')

    todos_los_usuarios = User.objects.all().order_by('username')

    paginator_users = Paginator(todos_los_usuarios, 4)
    users_page_1 = paginator_users.get_page(1)

    empleado = request.user.empleado 
    departamentos = Departamento.objects.all().order_by('nombre')
    estaciones = ServiceStation.objects.all().order_by('nombre')
    tipos_usuario = Group.objects.all().order_by('name')

    context = {
        'is_admin': is_admin,
        'empleado': empleado,
        'form_with_errors': form_with_errors,
        'form_usuario': form_usuario,
        'usuarios_generales': users_page_1,
        'departamentos': departamentos,
        'estaciones': estaciones,
        'tipos_usuario': tipos_usuario,
        'todos_los_usuarios': todos_los_usuarios,
    }
    return render(request, 'users.html', context)

@login_required
def SearchUsuarioView(request):
    page_number = request.GET.get('page', 1)
    query = request.GET.get('q', '')
    depto_id = request.GET.get('departamento_id', '')
    estacion_id = request.GET.get('estacion_id', '')
    is_admin = request.user.groups.filter(name='Administrador').exists()

    lookup = (
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )

    departamento_query = Q()
    if depto_id:
        departamento_query = Q(empleado__departamento__id=depto_id)
    
    estacion_query = Q()
    if estacion_id:
        estacion_query = Q(empleado__estacion_servicio__id=estacion_id) 

    usuarios_list = User.objects.filter(
        lookup,
        departamento_query,
        estacion_query,
        is_active=True,
    ).distinct().order_by('username')

    paginator = Paginator(usuarios_list, 4)
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
        template_name='_users_partial.html',
        context=
        {
            'usuarios': page_obj.object_list,
            'is_admin': is_admin
        },
        request=request
    ) 

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })

@login_required
@user_passes_test(is_admin_check)
def EditUsuarioView(request, pk):
    usuario_instance = get_object_or_404(User, id=pk)

    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, request.FILES, instance=usuario_instance, prefix='edit_usuario')
        
        if form.is_valid():
            # 1. Guardamos el usuario y lo asignamos a una variable
            usuario_actualizado = form.save()
            
            # --- NUEVA LÓGICA: Sincronizar Usuario -> Empleado ---
            # Verificamos si este usuario tiene un perfil de empleado asociado
            if hasattr(usuario_actualizado, 'empleado'):
                empleado = usuario_actualizado.empleado
                
                # Asignamos el estado dependiendo de si el usuario está activo o no.
                # Nota: Cambia 'INACTIVO' si en tu modelo usas otra palabra como 'BAJA'
                nuevo_estado = Empleado.EstadoEmpleado.ACTIVO if usuario_actualizado.is_active else 'INACTIVO'
                
                # Si los estados no coinciden, actualizamos el empleado
                if empleado.estado != nuevo_estado:
                    empleado.estado = nuevo_estado
                    empleado.save(update_fields=['estado'])
            # -----------------------------------------------------

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Usuario actualizado correctamente.'})
            
            messages.success(request, 'Usuario actualizado.')
            return redirect('users:users')
        else:
            # SI FALLA Y ES AJAX -> Mandamos los errores en JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            
            messages.error(request, 'Error al actualizar el usuario.')
    else:
        form = UsuarioEditForm(instance=usuario_instance, prefix='edit_usuario')

    return render(request, '_edit_usuario_form.html', {
        'form_usuario_edit': form,
        'usuario': usuario_instance
    })