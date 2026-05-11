"""

Django settings for config project.

"""



import os

from pathlib import Path

from datetime import timedelta

from dotenv import load_dotenv



BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')





def _read_secret(key):

    """Read a Docker secret from _FILE env var, falling back to the direct env var."""

    file_path = os.getenv(f'{key}_FILE')

    if file_path and os.path.isfile(file_path):

        with open(file_path, 'r') as f:

            return f.read().strip()

    return os.getenv(key, '')



# En production, mets cette clé dans une variable d'environnement

SECRET_KEY = _read_secret('SECRET_KEY') or os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-prod')



def env_bool(key, default=False):

    value = os.getenv(key)

    if value is None:

        return default

    return value.strip().lower() in {'1', 'true', 'yes', 'on'}





def env_list(key, default=''):

    return [item.strip() for item in os.getenv(key, default).split(',') if item.strip()]





# Quick-start development settings - unsuitable for production

# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/



# SECURITY WARNING: keep the secret key used in production secret!



DEBUG = env_bool('DEBUG', False)



ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if host.strip()]



# Current backend uses Django's default user model.

AUTH_USER_MODEL = 'auth.User'



INSTALLED_APPS = [

    'django.contrib.admin',

    'django.contrib.auth',

    'django.contrib.contenttypes',

    'django.contrib.sessions',

    'django.contrib.messages',

    'django.contrib.staticfiles',

    # rest framework 

    'rest_framework',

    'rest_framework_simplejwt.token_blacklist',

    # our app 

    'accounts',

    'project',

    'role',

    'tickets',

    'collaboration',

    ## jwt authentication 

    'corsheaders', 

    ## debug toolbar 

    "debug_toolbar",

    'drf_spectacular', 

    'orgs',

    'core',

    'activity',

    'search',

]



REST_FRAMEWORK = { 

    'DEFAULT_AUTHENTICATION_CLASSES': [

        'accounts.authentication.JWTAuthentication',

        'rest_framework.authentication.SessionAuthentication',

    ],

    'DEFAULT_PERMISSION_CLASSES': [

        'rest_framework.permissions.AllowAny',

    ],

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    }



MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # debug toolbar middleware 

    "debug_toolbar.middleware.DebugToolbarMiddleware", 

]



# CORS settings

CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', False)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = env_list(

    'CORS_ALLOWED_ORIGINS',

    'http://127.0.0.1:3000,http://localhost:3000'

)

CSRF_TRUSTED_ORIGINS = env_list(

    'CSRF_TRUSTED_ORIGINS',

    'http://127.0.0.1:3000,http://localhost:3000'

)

ROOT_URLCONF = 'config.urls'



TEMPLATES = [

    {

        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [BASE_DIR / "templates"],  # tu peux ajouter un dossier templates

        'APP_DIRS': True,

        'OPTIONS': {

            'context_processors': [

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

            ],

        },

    },

]



WSGI_APPLICATION = 'config.wsgi.application'



# Base de données - PostgreSQL in production, SQLite for local dev

if os.getenv('DB_HOST'):

    DATABASES = {

        'default': {

            'ENGINE': 'django.db.backends.postgresql',

            'NAME': os.getenv('DB_NAME', 'agileflow'),

            'USER': os.getenv('DB_USER', 'agileflow'),

            'PASSWORD': _read_secret('DB_PASSWORD'),

            'HOST': os.getenv('DB_HOST', 'localhost'),

            'PORT': os.getenv('DB_PORT', '5432'),

        }

    }

else:

    DATABASES = {

        'default': {

            'ENGINE': 'django.db.backends.sqlite3',

            'NAME': BASE_DIR / 'db.sqlite3',

        }

    }



# Validation des mots de passe

AUTH_PASSWORD_VALIDATORS = [

    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},

    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},

    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},

    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},

]



# Internationalisation

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



SIMPLE_JWT = {

    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    'AUTH_HEADER_TYPES': ('Bearer',),

    'ROTATE_REFRESH_TOKENS': True,

    'BLACKLIST_AFTER_ROTATION': True,

}



# Argon2id password hasher per spec (strongest available)

PASSWORD_HASHERS = [

    'django.contrib.auth.hashers.Argon2PasswordHasher',

    'django.contrib.auth.hashers.PBKDF2PasswordHasher',

    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',

]



# Celery configuration

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_SERIALIZER = 'json'

CELERY_RESULT_SERIALIZER = 'json'



# Security settings per spec

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_SAMESITE = 'Strict'

    CSRF_COOKIE_SAMESITE = 'Strict'



JWT_REFRESH_COOKIE = os.getenv('JWT_REFRESH_COOKIE', 'refresh_token')

JWT_ACCESS_COOKIE = os.getenv('JWT_ACCESS_COOKIE', 'access_token')

JWT_REFRESH_COOKIE_PATH = os.getenv('JWT_REFRESH_COOKIE_PATH', '/')

JWT_ACCESS_COOKIE_PATH = os.getenv('JWT_ACCESS_COOKIE_PATH', '/')

JWT_COOKIE_SECURE = env_bool('JWT_COOKIE_SECURE', not DEBUG)

JWT_COOKIE_HTTP_ONLY = env_bool('JWT_COOKIE_HTTP_ONLY', True)

JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Lax').capitalize()



if JWT_COOKIE_SAMESITE == 'None':

    JWT_COOKIE_SECURE = True





EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')

EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))

EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)

EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', False)

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')

EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@example.com')



OTP_EXPIRE_MINUTES = int(os.getenv('OTP_EXPIRE_MINUTES', 10))

OTP_DEV_RETURN_OTP = env_bool('OTP_DEV_RETURN_OTP', DEBUG)



# Static and media files

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'



MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'





# swagger add  settings for API documentation 

SPECTACULAR_SETTINGS = {

    'TITLE': 'My API',

    'DESCRIPTION': 'API for my project',

    'VERSION': '1.0.0',

}

