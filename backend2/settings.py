"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from .config import *  # pylint: disable=unused-wildcard-import

FROM_EMAIL = os.getenv('FROM_EMAIL')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = True


# Set to true if to run the public variant
RUN_AS_ADMIN_APP = os.getenv('RUN_AS_ADMIN_APP') == "True"

# For local development
if os.getenv('DEBUG'):
    EMAIL_HOST = 'mailcatcher'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# Application definition

SHARED_APPS = [
    'django_tenants',  # mandatory
    'tenants', # you must list the app where your tenant model resides in
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',

    'user',
]

TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',

    # Optional
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'core',
    'user',
    'mozilla_django_oidc',
    'ariadne.contrib.django',
    'django_elasticsearch_dsl',
    'notifications',
]

if LOCAL_APPS:
    TENANT_APPS += LOCAL_APPS

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

#if os.getenv('DEBUG'):
#    INSTALLED_APPS += ['elasticapm.contrib.django']


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

if not RUN_AS_ADMIN_APP:
    AUTHENTICATION_BACKENDS.append('core.auth.OIDCAuthBackend')

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.CustomLocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

if not RUN_AS_ADMIN_APP:
    MIDDLEWARE.append('mozilla_django_oidc.middleware.SessionRefresh')

if LOCAL_MIDDLEWARE:
    MIDDLEWARE += LOCAL_MIDDLEWARE

if os.getenv('DEBUG'):
    MIDDLEWARE = ['elasticapm.contrib.django.middleware.TracingMiddleware'] + MIDDLEWARE

ROOT_URLCONF = 'backend2.urls'
PUBLIC_SCHEMA_URLCONF = 'backend2.urls_public'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'backend2.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'user.User'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'mozilla_django_oidc': {
            'handlers': ['console'],
            'level': 'DEBUG'
        }
    }
}

if os.getenv('MEMCACHE_HOST_PORT'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': os.getenv('MEMCACHE_HOST_PORT'),
        }
    }


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = False

TIME_ZONE = 'Europe/Amsterdam'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

PASSWORD_RESET_TIMEOUT_DAYS = 1
ACCOUNT_ACTIVATION_DAYS = 7

if not RUN_AS_ADMIN_APP:
    LOGIN_URL = '/oidc/authenticate/'
    LOGIN_REDIRECT_URL = '/'
    LOGOUT_REDIRECT_URL = '/'

APPEND_SLASH = False

WEBPACK_DEV_SERVER = False

DEFAULT_FILE_STORAGE = "django_tenants.files.storage.TenantFileSystemStorage"

if SWIFT_ENABLED:
    DEFAULT_FILE_STORAGE = 'core.backends.tenant_swift_storage.TenantSwiftStorage'

if S3_ENABLED:
    DEFAULT_FILE_STORAGE = 'core.backends.tenant_s3_storage.TenantS3Boto3Storage'

#if os.getenv('DEBUG'):

#    ELASTIC_APM = {
    # Set required service name. Allowed characters:
    # a-z, A-Z, 0-9, -, _, and space
#        'SERVICE_NAME': 'apm-server',

    # Set custom APM Server URL (default: http://localhost:8200)
#        'SERVER_URL': 'http://apm-server:8200',
#        'DEBUG': True
#    }

ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.elasticsearch.CustomSignalProcessor'
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

TENANT_MODEL = "tenants.Client"

TENANT_DOMAIN_MODEL = "tenants.Domain"

IMPORTING = False
