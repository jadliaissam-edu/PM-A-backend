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



ALLOWED_HOSTS = ["*"]

# Current backend uses Django's default user model.

AUTH_USER_MODEL = 'auth.User'



INSTALLED_APPS = [
    'channels',
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
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
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
    'allauth.account.middleware.AccountMiddleware',
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
        'DIRS': [BASE_DIR / "templates"],
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
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Base de données (SQLite par défaut)
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

    SECURE_SSL_REDIRECT = False  # Disabled because Nginx handles the SSL redirect and terminates HTTPS!

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_SAMESITE = 'Strict'

    CSRF_COOKIE_SAMESITE = 'Strict'



JWT_REFRESH_COOKIE = os.getenv('JWT_REFRESH_COOKIE', 'refresh_token')

JWT_ACCESS_COOKIE = os.getenv('JWT_ACCESS_COOKIE', 'access_token')

JWT_REFRESH_COOKIE_PATH = os.getenv('JWT_REFRESH_COOKIE_PATH', '/')

JWT_ACCESS_COOKIE_PATH = os.getenv('JWT_ACCESS_COOKIE_PATH', '/')

# Cookie defaults:
# - In development (DEBUG=True) we use SameSite=Lax and Secure=False so cookies
#   work over plain HTTP during local testing.
# - In production (DEBUG=False) default to SameSite=None and Secure=True so
#   cross-site cookies are allowed and only sent over HTTPS.
default_samesite = 'Lax' if DEBUG else 'None'
JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', default_samesite).capitalize()
JWT_COOKIE_SECURE = env_bool('JWT_COOKIE_SECURE', not DEBUG)

JWT_COOKIE_HTTP_ONLY = env_bool('JWT_COOKIE_HTTP_ONLY', True)

# Ensure Secure is enforced in production when SameSite=None unless explicitly overridden.
if JWT_COOKIE_SAMESITE == 'None' and not DEBUG:
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

# Site and social auth settings
SITE_ID = int(os.getenv('SITE_ID', 1))

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Read OAuth client credentials from environment (.env)
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET') or os.getenv('GITHUB_SECRET')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/oauth/callback?provider=google')

LOGIN_REDIRECT_URL = os.getenv('LOGIN_REDIRECT_URL', '/')

# Optional provider config for django-allauth (keeps defaults minimal)
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': ['user:email'],
    }
}

# MinIO / S3 storage settings (for avatar/media storage)
USE_MINIO = env_bool('USE_MINIO', False)
if USE_MINIO:
    # Ensure django-storages[boto3] is installed
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_ENDPOINT_URL = os.getenv('MINIO_ENDPOINT', 'http://127.0.0.1:9000')
    AWS_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    AWS_STORAGE_BUCKET_NAME = os.getenv('MINIO_BUCKET', 'media')
    AWS_S3_REGION_NAME = os.getenv('MINIO_REGION', 'us-east-1')
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_ADDRESSING_STYLE = os.getenv('AWS_S3_ADDRESSING_STYLE', 'path')
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
