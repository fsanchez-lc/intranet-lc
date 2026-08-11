from django.db.models.signals import post_save

from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Empleado, Expediente

@receiver(post_save, sender=Empleado)
def create_user_for_new_employee(sender, instance, created, **kwargs):
    # **1. Evitar la creación/actualización si no es una nueva instancia**
    if not created:
        return # Si el Empleado ya existía, salimos de la función.

    # **2. Evitar el bucle de guardado recursivo**
    # Si el empleado ya tiene un usuario asociado (se estableció previamente), salimos.
    # Esto también sirve para no crear un usuario si ya se le asignó uno.
    if instance.user:
        return

    # Si llegamos aquí, es una nueva instancia de Empleado (created=True) que no tiene user asociado.
    
    # --- Lógica de Creación/Asignación de Usuario ---

    user = None # Inicializamos la variable user
    
    # 1. Obtener el username deseado (parte antes del @)
    # Ejemplo: 'empleado1@empresa.com.mx' -> 'empleado1'
    try:
        potential_username = instance.email.split('@')[0]
    except AttributeError:
        # Esto maneja si instance.email es None o no es una cadena
        print(f"ERROR: El empleado {instance.nombre} no tiene un email válido.")
        return # Salir si no hay email para continuar
    
    default_password = 'default-lc-pass' # Considera mover esto a settings o usar una variable de entorno

    # 2. Verificar si ya existe un User con ese email (opción de reutilización)
    if User.objects.filter(email=instance.email).exists():
        user = User.objects.get(email=instance.email)
    
    # 3. Crear el nuevo usuario si no existe uno con ese email
    else:
        # Asegurarse de que el username no esté ya en uso (aunque es menos probable si el email es único)
        # Si el username 'empleado1' ya está ocupado, Django.create_user generará un error 
        # a menos que uses una lógica más compleja para generar un username único (e.g., empleado1_1).
        # Para simplificar, asumimos que el email es único y, por ende, el username es casi único.
        
        try:
            user = User.objects.create_user(
                username=potential_username, # ¡Usamos la parte antes del @!
                email=instance.email,
                password=default_password,
                first_name=instance.nombre,
                # last_name=instance.apellido # Si tu modelo Empleado tiene apellido
            )
        except Exception as e:
            # Capturar si falla la creación (ej. username duplicado, aunque no debería si el email es único y el username se extrae de él)
            print(f"Error al crear el usuario para {instance.email}: {e}")
            return # Salir si la creación del usuario falla

    # 4. Asignar el usuario al Empleado y Guardar (¡Solo si se creó o asignó!)
    if user:
        # El único momento en que guardamos la instancia de Empleado es AQUÍ.
        # Esto es crucial para evitar el bucle recursivo.
        instance.user = user
        instance.save() 
        # NOTA: Esta llamada a .save() volverá a disparar la señal post_save, 
        # pero las validaciones al principio (instance.user y not created) lo detendrán.

        # --- Lógica de Asignación de Grupo ---
        try:
            # Busca el grupo. Si no existe, lo crea.
            empleado_group, _ = Group.objects.get_or_create(name="Empleado")
            # Añade el usuario a ese grupo
            user.groups.add(empleado_group)
            
        except Exception as e:
            print(f"Error al asignar grupo al usuario {user.username}: {e}")

@receiver(post_save, sender=Empleado)
def crear_documentos_base(sender, instance, created, **kwargs):
    if created:
        documentos_personales = [
            {
                'titulo': '1. Acta de nacimiento', 
                'tipo': 'Acta', 
                'requiere_firma': False,
                'categoria': 'personal',
                'descripcion': 'Copia de Acta de Nacimiento menor a 3 meses'
            },
            {
                'titulo': '2. Acta de matrimonio', 
                'tipo': 'Acta', 
                'requiere_firma': False,
                'categoria': 'personal',
                'descripcion': 'Copia de Acta de Matrimonio en dado caso de contar con ella.'
            },
            {
                'titulo': '3. Constancia de Último Grado de Estudios', 
                'tipo': 'constancia',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de la Constancia de Estudios del empleado'
            },
            {
                'titulo': '4. Número de Seguridad Social', 
                'tipo': 'identificacion',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia del Número de Seguridad Social menor a 3 meses'
            },
            {
                'titulo': '5. Antecedentes no penales', 
                'tipo': 'Constancia', 
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de Constancia de Antecedentes no Penales menor a 3 meses'
            },
            {
                'titulo': '6. Copia Comprobante de Domicilio', 
                'tipo': 'comprobante',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de la Identificación Oficial del empleado'
            },
            {
                'titulo': '7. Copia INE', 
                'tipo': 'identificacion',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de la Identificación Oficial del empleado'
            },
            {
                'titulo': '8. Copia CURP', 
                'tipo': 'identificacion',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de la Clave Única de Registro de Población del empleado'
            },
            {
                'titulo': '9. Cartas de Recomendación', 
                'tipo': 'documento',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de las Cartas de Recomendación del empleado'
            },
            {
                'titulo': '10. Copia de Licencia de Manejo Vigente', 
                'tipo': 'identificación',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Documento PDF o imagen de la Licencia de Manejo Vigente del empleado, en caso de contar con ella.'
            },
            {
                'titulo': '11. Certificado Médico', 
                'tipo': 'certificado',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia del Certificado Médico menor a 3 meses'
            },
            {
                'titulo': '12. Datos Generales del Personal Contratado', 
                'tipo': 'documento',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Documento llenado por el empleado sobre sus datos generales'
            },
            {
                'titulo': '13. Fotos del empleado', 
                'tipo': 'Comprobante',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': '6 fotos tamaño pasaporte a color con fondo blanco (no instantáneas)'
            },
            {
                'titulo': '14. Constancia de Situación Fiscal', 
                'tipo': 'certificado',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Copia de la Constancia de Situación Fiscal del empleado menor a 3 meses'
            },
            {
                'titulo': '15. Solicitud de Empleo o CV', 
                'tipo': 'documento',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Solicitud de Empleo o Curriculum Vitae del empleado'
            },
            {
                'titulo': '16. Estado de Cuenta Bancario', 
                'tipo': 'documento',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Documento PDF o imagen del Estado de Cuenta Bancario donde aparezca la CLABE del empleado.'
            },
            {
                'titulo': '17. Aviso de Retención de Infonavit', 
                'tipo': 'documento',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Aviso de Retención de Infonavit en caso de contar con algún crédito.'
            },
            {
                'titulo': '18. Ficha de Contratación de Personal', 
                'tipo': 'documento',
                'categoria': 'personal',
                'requiere_firma': False,
                'descripcion': 'Documento llenado por el empleado contratado sobre sus datos generales'
            },
        ]
        
        documentos_laborales = [
            {
                'titulo': '1. Contrato laboral', 
                'tipo': 'contrato', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original del contrato laboral'
            },
            {
                'titulo': '2. Convenio de confidencialidad', 
                'tipo': 'convenio', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original del convenio de confidencialidad firmado por el usuario'
            },
            {
                'titulo': '3. Pruebas psicométricas', 
                'tipo': 'documento', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Copia de las respuestas de las pruebas psicométricas iniciales del empleado'
            },
            {
                'titulo': '4. Alta de Colaborador en Sistemas', 
                'tipo': 'responsiva', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original de la responsiva de Acta de Colaborador en Sistemas',
                'ext': 'xlsx'
            },
            {
                'titulo': '5. Entrega de Equipos de TI - Celular', 
                'tipo': 'responsiva', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original de la responsiva de Entrega de Equipos de TI correspondiente al equipo celular'
            },
            {
                'titulo': '6. Entrega de Equipos de TI - Cómputo', 
                'tipo': 'responsiva', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original de la responsiva de Entrega de Equipos de TI correspondiente al equipo de cómputo'
            },
            {
                'titulo': '7. Entrega de Uniformes y Herramientas', 
                'tipo': 'responsiva', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original de la responsiva de Entrega de Uniformes y Herramientas'
            },
            {
                'titulo': '8. Carta de recepción y aceptación de documentos', 
                'tipo': 'responsiva', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original de la Carta de Recepción y Aceptación de Documentos firmada por el empleado'
            },
            {
                'titulo': '9. Manual de UPS', 
                'tipo': 'responsiva', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original del Manual de UPS firmado por el empleado'
            },
            {
                'titulo': '10. Solicitud de Reclutamiento de Personal', 
                'tipo': 'documento', 
                'requiere_firma': True,
                'categoria': 'laboral',
                'descripcion': 'Original de la Solicitud de Reclutamiento de Personal firmada por el solicitante y quien lo recibe'
            },
        ]

        todos_los_documentos = documentos_personales + documentos_laborales

        expedientes_a_crear = []
        for doc in todos_los_documentos:
            expedientes_a_crear.append(
                Expediente(
                    empleado=instance,
                    titulo=doc['titulo'],
                    tipo=doc['tipo'],
                    categoria=doc['categoria'],
                    requiere_firma=doc['requiere_firma'],
                    descripcion=doc.get('descripcion', ''),
                    archivo=None,
                    extension_plantilla=doc.get('ext', 'pdf')
                )
            )
        
        # Usamos bulk_create para optimizar (hace 1 sola consulta en vez de 20)
        Expediente.objects.bulk_create(expedientes_a_crear)