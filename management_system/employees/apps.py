from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employees'

    def ready(self):
        """
        Sobrescribe 'ready' para importar nuestras señales
        cuando la app esté lista.
        """
        import employees.signals  # <--- AÑADE ESTA LÍNEA