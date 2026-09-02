from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-xi)x+xcij$fd0w9_&0z6e7b^fz!=o6*w$0uv3z$9jt#!y_9za6'

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    '192.168.10.90',
    '192.168.10.59',
    'localhost'
]

LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard',
    'login',
    'navigation',
    'users',
    'equipment',
    'import_export',
    'employees',
    'service_stations',
    'tickets',
    'resources',
    'reports',
    "django_browser_reload",
    'guides',
    'administrator',
    'dinamicas',
    'channels',
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST", "redis"), 6379)],
        },
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

ROOT_URLCONF = 'management_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'navigation.utils.with_menu',
                'navigation.context_processors.contador_tareas_global',
            ],
        },
    },
]

WSGI_APPLICATION = 'management_system.wsgi.application'

ASGI_APPLICATION = 'management_system.asgi.application'
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'postgres',           # Nombre de la DB creada
#         'USER': 'sistemas_lc',           # Usuario creado
#         'PASSWORD': 'sistemas_lc_pass', # Contraseña del usuario
#         'HOST': 'localhost',                # Usar servidor local
#         'PORT': '5432',                     # Puerto por defecto
#     },
#      # --- CONFIGURACIÓN TEMPORAL DE SQLITE ---
#     'sqlite_original': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3', # Asegúrate que la ruta sea correcta
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Ruta base para guardar los archivos subidos por los usuarios
MEDIA_ROOT = BASE_DIR / 'media'

# URL pública para acceder a esos archivos
MEDIA_URL = '/media/'

X_FRAME_OPTIONS = 'SAMEORIGIN'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ==========================================
# CONFIGURACIÓN DE CORREO ELECTRÓNICO (SMTP cPanel)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Obtenemos las credenciales desde las variables de entorno
EMAIL_HOST = os.environ.get('EMAIL_HOST')           # ej. 'mail.tudominio.com'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465)) # 465 para SSL, 587 para TLS
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') # ej. 'notificaciones@tudominio.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Configuración de seguridad dependiendo del puerto
if EMAIL_PORT == 465:
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
elif EMAIL_PORT == 587:
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = True
