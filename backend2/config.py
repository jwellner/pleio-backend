import os
from django.utils.translation import ugettext_lazy as _

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'True'

ENV = os.getenv('ENV')

ALLOWED_HOSTS = [os.getenv('ALLOWED_HOST')]

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'HOST': os.getenv('DB_HOST'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'NAME': os.getenv('DB_NAME'),
    }
}

if os.getenv('ELGG_DB_HOST'):
    DATABASES["elgg_control"] = {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': os.getenv('ELGG_DB_HOST'),
        'USER': os.getenv('ELGG_DB_USER'),
        'PASSWORD': os.getenv('ELGG_DB_PASSWORD'),
        'NAME': os.getenv('ELGG_DB_NAME'),
    }

TIME_ZONE = 'UTC'

LOCAL_APPS = [
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
]

LOCAL_MIDDLEWARE = []

if not os.getenv('RUN_AS_ADMIN_APP'):
    LOCAL_MIDDLEWARE = ['core.middleware.UserLastOnlineMiddleware']

LANGUAGE_CODE = 'nl-NL'

LANGUAGES = [
    ('en', _('English')),
    ('nl', _('Dutch'))
]

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

# SWIFT FILE STORAGE
SWIFT_ENABLED = os.getenv('SWIFT_ENABLED') == 'True'
SWIFT_AUTH_URL = os.getenv('SWIFT_AUTH_URL')
SWIFT_USERNAME = os.getenv('SWIFT_USERNAME')
SWIFT_KEY = os.getenv('SWIFT_KEY')
SWIFT_CONTAINER_NAME = os.getenv('SWIFT_CONTAINER_NAME')
SWIFT_AUTO_CREATE_CONTAINER = os.getenv('SWIFT_AUTO_CREATE_CONTAINER') == 'True'
SWIFT_AUTO_CREATE_CONTAINER_PUBLIC = os.getenv('SWIFT_AUTO_CREATE_CONTAINER_PUBLIC') == 'True'
SWIFT_AUTO_BASE_URL = False
SWIFT_BASE_URL = "/file/download/"

# AWS s3 Storage
S3_ENABLED = os.getenv('S3_ENABLED') == 'True'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_DEFAULT_ACL = os.getenv('AWS_DEFAULT_ACL')

# Elasticsearch
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.getenv('ELASTICSEARCH_HOST')
    },
}

ELASTICSEARCH_DSL_INDEX_SETTINGS = {'number_of_shards': 1,
                                    'number_of_replicas': 0}
