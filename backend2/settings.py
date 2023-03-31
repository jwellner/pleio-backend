"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
# pragma: no cover
import os
from elasticapm.contrib.opentracing import Tracer
from opentracing import set_global_tracer

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'
ENV = os.getenv('ENV')
ALLOWED_HOSTS = [os.getenv('ALLOWED_HOST')]

CONTROL_PRIMARY_DOMAIN = os.getenv("CONTROL_PRIMARY_DOMAIN")

# Database
DATABASES = {
    'default': {
        'DATABASE': 'default',
        'ENGINE': 'django_tenants.postgresql_backend',
        'HOST': os.getenv('DB_HOST'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'NAME': os.getenv('DB_NAME'),
    },
}

if os.getenv('DB_HOST_REPLICA'):
    DATABASES["replica"] = {
        'DATABASE': 'replica',
        'ENGINE': 'django_tenants.postgresql_backend',
        'HOST': os.getenv('DB_HOST_REPLICA'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'NAME': os.getenv('DB_NAME'),
    }

OIDC_RP_CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET')
OIDC_RP_SCOPES = 'openid profile email'

OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv('OIDC_OP_AUTHORIZATION_ENDPOINT')
OIDC_OP_TOKEN_ENDPOINT = os.getenv('OIDC_OP_TOKEN_ENDPOINT')
OIDC_OP_USER_ENDPOINT = os.getenv('OIDC_OP_USER_ENDPOINT')
OIDC_OP_LOGOUT_ENDPOINT = os.getenv('OIDC_OP_LOGOUT_ENDPOINT')
PROFILE_PICTURE_URL = os.getenv('PROFILE_PICTURE_URL')
OIDC_OP_LOGOUT_URL_METHOD = 'core.auth.oidc_provider_logout'
OIDC_CALLBACK_CLASS = 'core.auth.OIDCAuthCallbackView'
OIDC_AUTHENTICATE_CLASS = 'core.auth.OIDCAuthenticateView'

# Elasticsearch
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.getenv('ELASTICSEARCH_HOST')
    },
}

ELASTICSEARCH_DSL_INDEX_SETTINGS = {'number_of_shards': 1,
                                    'number_of_replicas': 0}

ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.elasticsearch.CustomSignalProcessor'

EMAIL_DISABLED = os.getenv('EMAIL_DISABLED') == 'True'

FROM_EMAIL = os.getenv('FROM_EMAIL')
EMAIL_HOST = os.getenv('EMAIL_HOST')

if os.getenv('EMAIL_PORT'):
    EMAIL_PORT = os.getenv('EMAIL_PORT')

if os.getenv('AWS_SES_ACCESS_KEY_ID'):
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION_NAME')  # 'us-west-2'
    AWS_SES_REGION_ENDPOINT = os.getenv('AWS_SES_REGION_ENDPOINT')  # 'email.us-west-2.amazonaws.com'

    AWS_SES_ACCESS_KEY_ID = os.getenv('AWS_SES_ACCESS_KEY_ID')
    AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY')

# Set to true if to run the public variant
RUN_AS_ADMIN_APP = os.getenv('RUN_AS_ADMIN_APP') == "True"

# For local development
if DEBUG:
    EMAIL_HOST = 'mailcatcher'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False

if EMAIL_DISABLED:
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# Application definition

SHARED_APPS = [
    'django_tenants',  # mandatory
    'tenants',  # you must list the app where your tenant model resides in
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'db_mutex',
    'widget_tweaks',
    'user',
    'control',
    'post_deploy',
    # Fail-over for post-deploy
    'deploy_task',
]

TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',

    # Optional
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django_elasticsearch_dsl',
    'db_mutex',
    'mozilla_django_oidc',
    'ariadne_django',
    'post_deploy',
    'notifications',
    'autotranslate',
    'auditlog',
    'concierge',
    'core',
    'user',
    'external_content',
    'flow',
    'profile_sync',
    'blog',
    'cms',
    'discussion',
    'event',
    'news',
    'poll',
    'question',
    'wiki',
    'activity',
    'bookmark',
    'task',
    'file',
    'elgg',
    'pad',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

AUTHENTICATION_BACKENDS = ['core.auth.OIDCAuthBackend']

if RUN_AS_ADMIN_APP:
    AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

MIDDLEWARE = [
    'backend2.middleware.PleioTenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TENANT_MIDDLEWARE = [
    'core.middleware.TenantPrimaryDomainRedirectMiddleware',
    'core.middleware.CustomLocaleMiddleware',
    'core.middleware.AnonymousVisitorSessionMiddleware',
    'core.middleware.AcrCheckMiddleware',
    'core.middleware.UnsupportedBrowserMiddleware',
    'core.middleware.WalledGardenMiddleware',
    'core.middleware.OnboardingMiddleware',
    'core.middleware.RedirectMiddleware',
    'csp.middleware.CSPMiddleware',
    'core.middleware.CustomCSPMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'core.middleware.UserLastOnlineMiddleware',
]

if not RUN_AS_ADMIN_APP:
    MIDDLEWARE.extend(TENANT_MIDDLEWARE)

ROOT_URLCONF = 'backend2.urls'
PUBLIC_SCHEMA_URLCONF = 'backend2.urls_admin'

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
                'core.context_processor.config_processor',
                'csp.context_processors.nonce',
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

ENDPOINT_2FA = os.getenv('ENDPOINT_2FA', 'http://localhost:8001/securitypages')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'elasticapm': {
            'level': 'WARNING',
            'class': 'elasticapm.contrib.django.handlers.LoggingHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'mozilla_django_oidc': {
            'handlers': ['console'],
            'level': 'INFO'
        },
        # Log errors from the Elastic APM module to the console (recommended)
        'elasticapm.errors': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
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

TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'nl-NL'
LANGUAGES = [
    ('nl', 'Nederlands'),
    ('en', 'English'),
    ('de', 'Deutsch'),
    ('fr', 'Français'),
]

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

STATICFILES_DIRS = [
    ("frontend", os.path.join(BASE_DIR, 'static-frontend')),
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
if DEBUG:
    STATICFILES_STORAGE = 'core.staticfiles.PleioDevStaticFilesStorage'

PASSWORD_RESET_TIMEOUT_DAYS = 1
ACCOUNT_ACTIVATION_DAYS = 7

LOGIN_URL = '/oidc/authenticate/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
if RUN_AS_ADMIN_APP:
    LOGIN_URL = '/admin/login/'

APPEND_SLASH = False

WEBPACK_DEV_SERVER = False

DEFAULT_FILE_STORAGE = "django_tenants.files.storage.TenantFileSystemStorage"

MEDIA_ROOT = os.getenv("MEDIA_ROOT") if os.getenv("MEDIA_ROOT") else os.path.join(BASE_DIR, 'media/')
BACKUP_PATH = os.getenv("BACKUP_PATH") if os.getenv("BACKUP_PATH") else os.path.join(MEDIA_ROOT, 'backups/')

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
    'backend2.dbrouter.PrimaryReplicaRouter',
)

TENANT_MODEL = "tenants.Client"

TENANT_DOMAIN_MODEL = "tenants.Domain"

EXTRA_SET_TENANT_METHOD_PATH = "backend2.dbrouter.extra_set_tenant_method"

# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')

# Added because of: https://github.com/celery/celery/issues/4296
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
}
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER') == 'True'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_PUBLISH_RETRY = True
CELERY_TASK_PUBLISH_RETRY_POLICY = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2
}
CELERY_TIMEZONE = 'Europe/Amsterdam'

APM_ENABLED = os.getenv('APM_ENABLED') == 'True'
APM_OPENTRACING_ENABLED = os.getenv('APM_OPENTRACING_ENABLED') == 'True'

if APM_ENABLED:
    INSTALLED_APPS += ['elasticapm.contrib.django']
    ELASTIC_APM = {
        'SERVICE_NAME': os.getenv('APM_SERVICE_NAME'),
        'ENVIRONMENT': ENV,
        'SECRET_TOKEN': os.getenv('APM_TOKEN'),
        'SERVER_URL': os.getenv('APM_SERVER_URL'),
        'VERIFY_SERVER_CERT': os.getenv('APM_VERIFY_SERVER_CERT') != "False",
        'DEBUG': True,
    }

    if APM_OPENTRACING_ENABLED:
        set_global_tracer(Tracer(config=ELASTIC_APM))

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CLAMAV_HOST = os.getenv('CLAMAV_HOST', None)

BOUNCER_URL = os.getenv('BOUNCER_URL', None)
BOUNCER_TOKEN = os.getenv('BOUNCER_TOKEN', None)

ACCOUNT_API_URL = os.getenv('ACCOUNT_API_URL', None)
ACCOUNT_API_TOKEN = os.getenv('ACCOUNT_API_TOKEN', None)
ACCOUNT_SYNC_ENABLED = os.getenv('ACCOUNT_SYNC_ENABLED') == 'True'
ACCOUNT_DATA_EXPIRE = os.getenv('ACCOUNT_DATA_EXPIRE') or 5

SECURE_REFERRER_POLICY = 'origin-when-cross-origin'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Content-Security-Policy header configuration https://django-csp.readthedocs.io/en/latest/configuration.html
CSP_DEFAULT_SRC = ["'self'"]
CSP_BASE_URI = ["'none'"]
CSP_OBJECT_SRC = ["'none'"]
CSP_IMG_SRC = [
    "'self'",
    "data:",
    "https://statistiek.rijksoverheid.nl",
    "https://www.google-analytics.com",
    "https://i.ytimg.com",
    "https://i.vimeocdn.com",
    "https://*.pleio.nl"
]
if PROFILE_PICTURE_URL:
    CSP_IMG_SRC.append(PROFILE_PICTURE_URL)

# Inline CSS is used on sites so we need to allow it
CSP_STYLE_SRC = [
    "'self'",
    "'unsafe-inline'",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com"
]
CSP_FONT_SRC = [
    "'self'",
    "https://fonts.gstatic.com"
]
# Using unsafe-inline is not safe so we choose to use strict-dynamic (https://csp.withgoogle.com/docs/index.html)
# CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "https://stats.pleio.nl", "https://statistiek.rijksoverheid.nl"]
CSP_INCLUDE_NONCE_IN = ['script-src']
CSP_SCRIPT_SRC = [
    "'unsafe-inline'",
    "'strict-dynamic'",
    "https:",
    "http:"
]  # for backward compatibility with older browsers that don't support strict-dynamic
CSP_CONNECT_SRC = [
    "'self'",
    "https://stats.pleio.nl",
    "https://statistiek.rijksoverheid.nl",
    "https://www.google-analytics.com",
    "https://vimeo.com",
]
CSP_FRAME_SRC = [
    "'self'",
    "https://www.youtube-nocookie.com",
    "https://player.vimeo.com",
    "https://api.eu.kaltura.com",
    "https://*.pleio.nl",
    "https://feed.mikle.com"
]
# Add csp.contrib.rate_limiting.RateLimitedCSPMiddleware middleware when enabling reporting
# CSP_REPORT_URI = "/report-csp-violation"
# CSP_REPORT_PERCENTAGE = 1 if DEBUG else 0.1

# When DEBUG is on we don't require HTTPS on our resources because in a local environment
CSP_UPGRADE_INSECURE_REQUESTS = not DEBUG
CSP_REPORT_ONLY = os.getenv('CSP_REPORT_ONLY') == 'True'

if DEBUG:
    # Add for local development
    CSP_REPORT_ONLY = True
    CSP_STYLE_SRC.append("http://localhost:9001")
    CSP_SCRIPT_SRC.append("http://localhost:9001")
    CSP_FONT_SRC.append("http://frontend-dev-server:9001")
    CSP_CONNECT_SRC.append("http://frontend-dev-server:9001")
    CSP_CONNECT_SRC.append("ws://frontend-dev-server:9001")

AUTOTRANSLATE_TRANSLATOR_SERVICE = 'core.services.translate_service.DeeplTranslatorService'
DEEPL_TOKEN = os.getenv('DEEPL_TOKEN', None)

POST_DEPLOY_CELERY_APP = 'backend2.celery.app'
POST_DEPLOY_SCHEDULER_MANAGER = 'post_deploy.plugins.scheduler.celery.CeleryScheduler'
POST_DEPLOY_CONTEXT_MANAGER = 'post_deploy.plugins.context.tenant.TenantContext'

SILENCED_SYSTEM_CHECKS = [
    # Warning at auditlog.LogEntry.additional_data
    # For more information: run the application without this line.
    'django_jsonfield_backport.W001'
]

ONLINE_MEETINGS_SETTINGS_CONTAINER = 'core.meetings.SettingsContainer'
ONLINE_MEETINGS_URL = os.getenv("ONLINE_MEETINGS_URL")
VIDEO_CALL_RESERVE_ROOM_URL = os.getenv("VIDEO_CALL_RESERVE_ROOM_URL")

USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": os.getenv("VAPID_PUBLIC_KEY"),
    "VAPID_PRIVATE_KEY": os.getenv("VAPID_PRIVATE_KEY"),
    "VAPID_ADMIN_EMAIL": os.getenv("VAPID_ADMIN_EMAIL")
}

EXTERNAL_CONTENT_AUTHOR_EMAIL = "externalcontent@localhost"
DB_MUTEX_TTL_SECONDS = 3600 * 6

BLEACH_EMAIL_TAGS = [
    "br", "p",
    "h2", "h3", "h4", "h5",
    "strong", "em", "u",
]
BLEACH_EMAIL_ATTRIBUTES = {
    "*": [],
}

SCAN_CYCLE_DAYS = os.getenv("SCAN_CYCLE_DAYS") or 120